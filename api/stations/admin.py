from django.contrib import admin
from .models import Station, Brand, Episode, Book

# Register your models here.
admin.site.register([Station, Brand, Episode, Book])
