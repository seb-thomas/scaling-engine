from django.db import models
from django.utils.text import slugify
from django.utils import timezone
import json


class Station(models.Model):
    name = models.CharField(max_length=120)
    station_id = models.CharField(max_length=120, default="")
    url = models.URLField()
    description = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Brand(models.Model):
    station = models.ForeignKey(Station, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    url = models.URLField()
    description = models.TextField(blank=True, default="")
    brand_color = models.CharField(max_length=7, blank=True, default="")
    producer_name = models.CharField(max_length=120, blank=True, default="")
    producer_url = models.URLField(blank=True, default="")
    spider_name = models.CharField(max_length=120, blank=True, default="bbc_episodes")
    created = models.DateTimeField(auto_now_add=True)

    @property
    def book_count(self):
        """Count of verified books associated with this brand"""
        return Book.objects.filter(
            episodes__brand=self,
            verification_status=Book.VERIFICATION_VERIFIED,
        ).distinct().count()

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if not provided
        if not self.slug and self.name:
            base_slug = slugify(self.name) or f"brand-{self.id or 0}"
            self.slug = base_slug
            # Ensure uniqueness
            counter = 1
            while (
                Brand.objects.filter(slug=self.slug)
                .exclude(pk=self.pk if self.pk else None)
                .exists()
            ):
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Episode(models.Model):
    STAGE_SCRAPED = "SCRAPED"
    STAGE_EXTRACTION_QUEUED = "EXTRACTION_QUEUED"
    STAGE_EXTRACTING = "EXTRACTING"
    STAGE_EXTRACTION_NO_BOOKS = "EXTRACTION_NO_BOOKS"
    STAGE_EXTRACTION_FAILED = "EXTRACTION_FAILED"
    STAGE_VERIFICATION_QUEUED = "VERIFICATION_QUEUED"
    STAGE_VERIFICATION_FAILED = "VERIFICATION_FAILED"
    STAGE_REVIEW = "REVIEW"
    STAGE_COMPLETE = "COMPLETE"
    STAGE_CHOICES = [
        (STAGE_SCRAPED, "Scraped"),
        (STAGE_EXTRACTION_QUEUED, "Extraction Queued"),
        (STAGE_EXTRACTING, "Extracting"),
        (STAGE_EXTRACTION_NO_BOOKS, "No Books Found"),
        (STAGE_EXTRACTION_FAILED, "Extraction Failed"),
        (STAGE_VERIFICATION_QUEUED, "Verification Queued"),
        (STAGE_VERIFICATION_FAILED, "Verification Failed"),
        (STAGE_REVIEW, "Needs Review"),
        (STAGE_COMPLETE, "Complete"),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    url = models.URLField(default="", unique=True)
    aired_at = models.DateTimeField(blank=True, null=True)

    # Snapshot + pipeline (merged from RawEpisodeData)
    scraped_data = models.JSONField(null=True, blank=True)
    stage = models.CharField(
        max_length=25, choices=STAGE_CHOICES, default=STAGE_SCRAPED
    )
    processed_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    extraction_result = models.JSONField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)

    @classmethod
    def stuck(cls, threshold_minutes=60):
        """Return episodes stuck in EXTRACTION_QUEUED/EXTRACTING longer than threshold."""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(minutes=threshold_minutes)
        return cls.objects.filter(
            stage__in=[cls.STAGE_EXTRACTION_QUEUED, cls.STAGE_EXTRACTING],
            status_changed_at__lt=cutoff,
        )

    def compute_stage_after_extraction(self):
        """Called after AI extraction. Books are candidates — go to VERIFICATION_QUEUED."""
        if not self.books.exists():
            return self.STAGE_EXTRACTION_NO_BOOKS
        return self.STAGE_VERIFICATION_QUEUED

    def compute_stage_after_verification(self):
        """Called after verify_pending_books. Only now do we evaluate confidence + results."""
        if self.stage == self.STAGE_COMPLETE:
            return self.STAGE_COMPLETE  # admin sign-off is sticky
        books = self.books.all()
        if not books.exists():
            return self.STAGE_EXTRACTION_NO_BOOKS
        if books.filter(verification_status='not_found').exists():
            return self.STAGE_REVIEW
        if books.filter(verification_status='pending').exists():
            return self.STAGE_VERIFICATION_QUEUED
        # All books verified — the sanity check during verification
        # already guards against wrong matches, so trust the result.
        return self.STAGE_COMPLETE

    def save(self, *args, **kwargs):
        # Auto-generate slug from title if not provided
        if not self.slug and self.title:
            base_slug = slugify(self.title) or f"episode-{self.id or 0}"
            self.slug = base_slug
            # Ensure uniqueness
            counter = 1
            while (
                Episode.objects.filter(slug=self.slug)
                .exclude(pk=self.pk if self.pk else None)
                .exists()
            ):
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


def book_cover_path(instance, filename):
    """Generate upload path for book covers: covers/brand-slug/author-title.ext"""
    import os

    ext = os.path.splitext(filename)[1] or ".jpg"
    first_episode = instance.episodes.select_related("brand").first() if instance.pk else None
    brand_slug = (
        first_episode.brand.slug
        if first_episode and first_episode.brand
        else "unknown"
    )
    return f"covers/{brand_slug}/{instance.slug}{ext}"


class Topic(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name_plural = "topics"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    VERIFICATION_PENDING = "pending"
    VERIFICATION_VERIFIED = "verified"
    VERIFICATION_NOT_FOUND = "not_found"
    VERIFICATION_CHOICES = [
        (VERIFICATION_PENDING, "Pending"),
        (VERIFICATION_VERIFIED, "Verified"),
        (VERIFICATION_NOT_FOUND, "Not found"),
    ]

    episodes = models.ManyToManyField(Episode, related_name="books", blank=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    author = models.CharField(max_length=255, blank=True, default="")
    topics = models.ManyToManyField(Topic, blank=True)
    description = models.TextField(blank=True, default="")
    cover_image = models.ImageField(
        upload_to=book_cover_path,
        blank=True,
        null=True,
        help_text="Book cover image stored locally",
    )
    cover_fetch_error = models.TextField(blank=True, default="")
    purchase_link = models.URLField(blank=True, default="")
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_CHOICES,
        default=VERIFICATION_PENDING,
    )
    verification_checked_at = models.DateTimeField(null=True, blank=True)
    unmatched_topics = models.CharField(max_length=255, blank=True, default="")

    def _generate_slug(self):
        """Generate slug from author + title, ensuring uniqueness."""
        if self.author:
            slug_source = f"{self.author} {self.title}"
        else:
            slug_source = self.title
        base_slug = slugify(slug_source) or f"book-{self.id or 0}"
        slug = base_slug
        counter = 1
        while (
            Book.objects.filter(slug=slug)
            .exclude(pk=self.pk if self.pk else None)
            .exists()
        ):
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def save(self, *args, **kwargs):
        if self.title:
            expected_slug = self._generate_slug()
            if not self.slug or self.slug != expected_slug:
                self.slug = expected_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        episode = self.episodes.select_related("brand").first()
        brand_slug = episode.brand.slug if episode and episode.brand else "unknown"
        return f"https://radioreads.fun/{brand_slug}/{self.slug}"

    def get_bookshop_affiliate_url(self):
        """Generate Bookshop.org affiliate search URL for this book"""
        from .utils import generate_bookshop_affiliate_url

        return generate_bookshop_affiliate_url(self.title, self.author)


class Phrase(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
