from django.db import models
from django.utils.text import slugify
import json


class Station(models.Model):
    name = models.CharField(max_length=120)
    station_id = models.CharField(max_length=120, default="")
    url = models.URLField()
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
    created = models.DateTimeField(auto_now_add=True)

    @property
    def book_count(self):
        """Count of books associated with this brand"""
        return Book.objects.filter(episode__brand=self).count()

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
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    url = models.URLField(default="", unique=True)
    aired_at = models.DateTimeField(blank=True, null=True)
    has_book = models.BooleanField(default=False, editable=False)

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
    brand_slug = instance.episode.brand.slug if instance.episode and instance.episode.brand else "unknown"
    return f"covers/{brand_slug}/{instance.slug}{ext}"


class Book(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    author = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    cover_image = models.ImageField(
        upload_to=book_cover_path, blank=True, null=True,
        help_text="Book cover image stored locally"
    )
    purchase_link = models.URLField(blank=True, default="")

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


class RawEpisodeData(models.Model):
    """Store raw scraped data from BBC before AI processing"""

    episode = models.OneToOneField(
        Episode, on_delete=models.CASCADE, related_name="raw_data"
    )
    scraped_data = models.JSONField(default=dict)
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Raw data for {self.episode.title}"


class Phrase(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
