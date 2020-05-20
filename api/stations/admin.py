from django.contrib import admin
from .models import Station, Brand, Episode, Book, Phrase

# Register your models here.
admin.site.register([Station, Brand, Episode, Book, Phrase])
