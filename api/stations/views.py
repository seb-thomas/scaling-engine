from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from django.db import connection
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
import redis

from .serializers import StationSerializer, BookSerializer, BrandShowSerializer
from .models import Station, Book, Brand


class StationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StationSerializer
    queryset = Station.objects.all()
    lookup_field = "station_id"

    def get_queryset(self):
        queryset = Station.objects.all()
        station_id = self.request.query_params.get("station_id", None)
        if station_id:
            queryset = queryset.filter(station_id=station_id)
        return queryset


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandShowSerializer
    queryset = Brand.objects.select_related("station").all()
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created"]

    def get_queryset(self):
        queryset = Brand.objects.select_related("station").annotate(
            annotated_book_count=Count("episode__book")
        )
        station_id = self.request.query_params.get("station_id", None)
        if station_id:
            queryset = queryset.filter(station__station_id=station_id)
        return queryset

    @action(detail=True, methods=["get"])
    def books(self, request, pk=None):
        brand = self.get_object()
        books = (
            Book.objects.filter(episode__brand=brand)
            .select_related("episode", "episode__brand", "episode__brand__station")
            .order_by("-episode__aired_at", "-episode__id")
        )

        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 10))
        paginator = Paginator(books, page_size)
        page_obj = paginator.get_page(page)

        serializer = BookSerializer(page_obj, many=True)
        return Response(
            {
                "count": paginator.count,
                "next": page_obj.next_page_number() if page_obj.has_next() else None,
                "previous": (
                    page_obj.previous_page_number() if page_obj.has_previous() else None
                ),
                "results": serializer.data,
            }
        )


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BookSerializer
    queryset = Book.objects.select_related(
        "episode", "episode__brand", "episode__brand__station"
    ).all()
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["title", "author", "description"]
    ordering_fields = ["episode__aired_at", "episode__id"]
    ordering = ["-episode__id"]

    def get_queryset(self):
        queryset = super().get_queryset()
        brand_id = self.request.query_params.get("brand", None)
        if brand_id:
            queryset = queryset.filter(episode__brand__id=brand_id)
        brand_slug = self.request.query_params.get("brand_slug", None)
        if brand_slug:
            queryset = queryset.filter(episode__brand__slug=brand_slug)
        station_id = self.request.query_params.get("station_id", None)
        if station_id:
            queryset = queryset.filter(episode__brand__station__station_id=station_id)
        return queryset


def health_check(request):
    """Health check endpoint that verifies DB and Redis connectivity"""
    import os

    status = {"status": "healthy", "checks": {}}

    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            status["checks"]["database"] = "ok"
    except Exception as e:
        status["status"] = "unhealthy"
        status["checks"]["database"] = f"error: {str(e)}"

    # Check Redis connection
    try:
        redis_url = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
        r = redis.from_url(redis_url)
        r.ping()
        status["checks"]["redis"] = "ok"
    except Exception as e:
        status["status"] = "unhealthy"
        status["checks"]["redis"] = f"error: {str(e)}"

    # Return appropriate HTTP status
    http_status = 200 if status["status"] == "healthy" else 503
    return JsonResponse(status, status=http_status)
