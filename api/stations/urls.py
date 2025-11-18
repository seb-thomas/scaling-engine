from django.urls import path
from . import views

app_name = "stations"

urlpatterns = [
    path("", views.index, name="index"),
    path("book/<int:book_id>/", views.book_detail, name="book_detail"),
]
