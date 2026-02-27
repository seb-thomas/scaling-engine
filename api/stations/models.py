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
        """Count of books associated with this brand"""
        return Book.objects.filter(episodes__brand=self).distinct().count()

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
    STATUS_SCRAPED = "SCRAPED"
    STATUS_QUEUED = "QUEUED"
    STATUS_PROCESSING = "PROCESSING"
    STATUS_PROCESSED = "PROCESSED"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = [
        (STATUS_SCRAPED, "Scraped"),
        (STATUS_QUEUED, "Queued"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_PROCESSED, "Processed"),
        (STATUS_FAILED, "Failed"),
    ]

    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    url = models.URLField(default="", unique=True)
    aired_at = models.DateTimeField(blank=True, null=True)
    has_book = models.BooleanField(default=False, editable=False)

    # Snapshot + pipeline (merged from RawEpisodeData)
    scraped_data = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_SCRAPED
    )
    processed_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    extraction_result = models.JSONField(null=True, blank=True)
    ai_confidence = models.FloatField(null=True, blank=True)
    status_changed_at = models.DateTimeField(null=True, blank=True)

    REVIEW_NOT_REQUIRED = "NOT_REQUIRED"
    REVIEW_REQUIRED = "REQUIRED"
    REVIEW_REVIEWED = "REVIEWED"
    REVIEW_CHOICES = [
        ("", "Unprocessed"),
        (REVIEW_NOT_REQUIRED, "Not required"),
        (REVIEW_REQUIRED, "Required"),
        (REVIEW_REVIEWED, "Reviewed"),
    ]
    review_status = models.CharField(
        max_length=20, choices=REVIEW_CHOICES, blank=True, default=""
    )

    @classmethod
    def stuck(cls, threshold_minutes=60):
        """Return episodes stuck in QUEUED/PROCESSING longer than threshold."""
        from datetime import timedelta
        cutoff = timezone.now() - timedelta(minutes=threshold_minutes)
        return cls.objects.filter(
            status__in=[cls.STATUS_QUEUED, cls.STATUS_PROCESSING],
            status_changed_at__lt=cutoff,
        )

    def compute_review_status(self):
        """Determine review status based on extraction signals.
        Does not overwrite REVIEWED — only sets REQUIRED or NOT_REQUIRED."""
        if self.review_status == self.REVIEW_REVIEWED:
            return self.review_status
        if self.ai_confidence is None:
            return ""
        if self.ai_confidence < 0.9:
            return self.REVIEW_REQUIRED
        if self.books.filter(google_books_verified=False).exists():
            return self.REVIEW_REQUIRED
        return self.REVIEW_NOT_REQUIRED

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


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(models.Model):
    episodes = models.ManyToManyField(Episode, related_name="books", blank=True)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    author = models.CharField(max_length=255, blank=True, default="")
    categories = models.ManyToManyField(Category, blank=True)
    description = models.TextField(blank=True, default="")
    cover_image = models.ImageField(
        upload_to=book_cover_path,
        blank=True,
        null=True,
        help_text="Book cover image stored locally",
    )
    cover_fetch_error = models.TextField(blank=True, default="")
    purchase_link = models.URLField(blank=True, default="")
    google_books_verified = models.BooleanField(default=False)
    unmatched_categories = models.CharField(max_length=255, blank=True, default="")

    def save(self, *args, **kwargs):
        # Auto-generate slug from author + title if not provided
        if not self.slug and self.title:
            # Include author in slug for better URLs (e.g., alan-hollinghurst-the-line-of-beauty)
            if self.author:
                slug_source = f"{self.author} {self.title}"
            else:
                slug_source = self.title
            base_slug = slugify(slug_source) or f"book-{self.id or 0}"
            self.slug = base_slug
            # Ensure uniqueness
            counter = 1
            while (
                Book.objects.filter(slug=self.slug)
                .exclude(pk=self.pk if self.pk else None)
                .exists()
            ):
                self.slug = f"{base_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_bookshop_affiliate_url(self):
        """Generate Bookshop.org affiliate search URL for this book"""
        from .utils import generate_bookshop_affiliate_url

        return generate_bookshop_affiliate_url(self.title, self.author)


class Phrase(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
