from django.db import models

# Create your models here.


class Station(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return "/stations/{}/".format(self.pk)
