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
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Episode(models.Model):
    brand = models.ForeignKey(
        Brand, on_delete=models.CASCADE, default=None, blank=True, null=True
    )
    title = models.CharField(max_length=255)
    url = models.URLField(default="")

    def __str__(self):
        return self.title


class Book(models.Model):
    episode = models.ForeignKey(Episode, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    def __str__(self):
        return self.title
