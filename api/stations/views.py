from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.db.models import Prefetch
from rest_framework import viewsets

from .serializers import StationSerializer
from .models import Station, Book, Episode, Brand


class StationView(viewsets.ModelViewSet):
    serializer_class = StationSerializer
    queryset = Station.objects.all()


def index(request):
    """Homepage showing all discovered books"""
    books = Book.objects.select_related(
        'episode',
        'episode__brand',
        'episode__brand__station'
    ).order_by('-episode__id')

    context = {
        "books": books,
        "total_books": books.count(),
    }
    return render(request, "stations/index.html", context)


def book_detail(request, book_id):
    """Individual book detail page"""
    book = get_object_or_404(
        Book.objects.select_related(
            'episode',
            'episode__brand',
            'episode__brand__station'
        ),
        pk=book_id
    )
    return render(request, "stations/book_detail.html", {"book": book})
