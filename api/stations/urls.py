from django.urls import path
from . import views

app_name = "stations"

urlpatterns = [
    path("", views.index, name="index"),
    path("station/<str:station_id>/", views.station_detail, name="station_detail"),
    path("show/<slug:slug>/", views.show_detail, name="show_detail"),
    path("book/<slug:slug>/", views.book_detail, name="book_detail"),
]
