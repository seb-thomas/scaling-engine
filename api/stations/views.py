from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q, Count
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import StationSerializer, BookSerializer, BrandShowSerializer
from .models import Station, Book, Episode, Brand


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StationSerializer
    queryset = Station.objects.all()
    lookup_field = 'station_id'
    
    def get_queryset(self):
        queryset = Station.objects.all()
        station_id = self.request.query_params.get('station_id', None)
        if station_id:
            queryset = queryset.filter(station_id=station_id)
        return queryset


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandShowSerializer
    queryset = Brand.objects.select_related('station').all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created']
    
    def get_queryset(self):
        queryset = Brand.objects.select_related('station').annotate(
            annotated_book_count=Count('episode__book')
        )
        station_id = self.request.query_params.get('station_id', None)
        if station_id:
            queryset = queryset.filter(station__station_id=station_id)
        return queryset
    
    @action(detail=True, methods=['get'])
    def books(self, request, pk=None):
        brand = self.get_object()
        books = Book.objects.filter(
            episode__brand=brand
        ).select_related(
            'episode',
            'episode__brand',
            'episode__brand__station'
        ).order_by('-episode__aired_at', '-episode__id')
        
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        paginator = Paginator(books, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = BookSerializer(page_obj, many=True)
        return Response({
            'count': paginator.count,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'results': serializer.data
        })


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.select_related(
        'episode',
        'episode__brand',
        'episode__brand__station'
    ).all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'description']
    ordering_fields = ['episode__aired_at', 'episode__id']
    ordering = ['-episode__id']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        brand_id = self.request.query_params.get('brand', None)
        if brand_id:
            queryset = queryset.filter(episode__brand__id=brand_id)
        return queryset


# Keep template views for backward compatibility during migration
def index(request):
    """Homepage showing all discovered books"""
    books = Book.objects.select_related(
        'episode',
        'episode__brand',
        'episode__brand__station'
    ).order_by('-episode__id')
    
    # Pagination - 10 books per page
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all brands for "All Shows" section
    brands = Brand.objects.select_related('station').all().order_by('station__name', 'name')
    
    # Get all stations for navigation
    stations = Station.objects.all().order_by('name')

    context = {
        "books": page_obj,
        "page_obj": page_obj,
        "total_books": books.count(),
        "brands": brands,
        "stations": stations,
    }
    return render(request, "stations/index.html", context)


def station_detail(request, station_id):
    """Station detail page showing all shows for a station"""
    station = get_object_or_404(Station, station_id=station_id)
    brands = Brand.objects.filter(station=station).order_by('name')
    
    # Get all stations for navigation
    stations = Station.objects.all().order_by('name')
    
    # Breadcrumbs
    breadcrumb_items = [
        {'label': 'Home', 'href': '/'},
        {'label': station.name}
    ]
    
    context = {
        "station": station,
        "brands": brands,
        "stations": stations,
        "breadcrumb_items": breadcrumb_items,
    }
    return render(request, "stations/station_detail.html", context)


def show_detail(request, show_id):
    """Show detail page showing all books for a show/brand"""
    brand = get_object_or_404(
        Brand.objects.select_related('station'),
        pk=show_id
    )
    
    books = Book.objects.filter(
        episode__brand=brand
    ).select_related(
        'episode',
        'episode__brand',
        'episode__brand__station'
    ).order_by('-episode__aired_at', '-episode__id')
    
    # Pagination - 10 books per page
    paginator = Paginator(books, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all stations for navigation
    stations = Station.objects.all().order_by('name')
    
    # Breadcrumbs
    breadcrumb_items = [
        {'label': 'Home', 'href': '/'},
        {'label': brand.station.name, 'href': f'/station/{brand.station.station_id}/'},
        {'label': brand.name}
    ]
    
    context = {
        "show": brand,
        "books": page_obj,
        "page_obj": page_obj,
        "stations": stations,
        "breadcrumb_items": breadcrumb_items,
    }
    return render(request, "stations/show_detail.html", context)


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
    
    # Get all stations for navigation
    stations = Station.objects.all().order_by('name')
    
    # Breadcrumbs
    breadcrumb_items = [
        {'label': 'Home', 'href': '/'},
        {'label': book.episode.brand.station.name, 'href': f'/station/{book.episode.brand.station.station_id}/'},
        {'label': book.episode.brand.name, 'href': f'/show/{book.episode.brand.id}/'},
        {'label': book.title}
    ]
    
    context = {
        "book": book,
        "stations": stations,
        "breadcrumb_items": breadcrumb_items,
    }
    return render(request, "stations/book_detail.html", context)
