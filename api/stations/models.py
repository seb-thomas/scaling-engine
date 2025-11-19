from django.db import models


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
    url = models.URLField()
    description = models.TextField(blank=True, default="")
    created = models.DateTimeField(auto_now_add=True)

    @property
    def book_count(self):
        """Count of books associated with this brand"""
        return Book.objects.filter(episode__brand=self).count()

    def __str__(self):
        return self.name


class Episode(models.Model):
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    title = models.CharField(max_length=255)
    url = models.URLField(default="", unique=True)
    description = models.TextField(blank=True, default="")
    aired_at = models.DateTimeField(blank=True, null=True)
    has_book = models.BooleanField(default=False, editable=False)

    def __str__(self):
        return self.title


class Book(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, default="")
    description = models.TextField(blank=True, default="")
    cover_image = models.URLField(blank=True, default="")

    def __str__(self):
        return self.title


class Phrase(models.Model):
    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
