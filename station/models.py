from django.db import models

# Create your models here.
class Station(models.Model):
    name = models.CharField(max_length=120)
    url = models.URLField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_delete_url(self):
        return "/stations/{}/delete".format(self.pk)

    def get_update_url(self):
        return "/stations/{}/update".format(self.pk)

    def get_absolute_url(self):
        return "/stations/{}/".format(self.pk)
