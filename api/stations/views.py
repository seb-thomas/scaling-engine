from django.http import Http404, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count, F
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import StationSerializer, BookSerializer, BrandShowSerializer
from .models import Station, Book, Brand, Category


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
            .order_by(F("episode__aired_at").desc(nulls_last=True), "-episode__id")
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
    ).prefetch_related("categories").all()
    lookup_field = "slug"
    filter_backends = [filters.SearchFilter]
    search_fields = ["title", "author", "categories__name"]

    def get_queryset(self):
        queryset = super().get_queryset().order_by(
            F("episode__aired_at").desc(nulls_last=True),
            "-episode__id",
        )
        brand_id = self.request.query_params.get("brand", None)
        if brand_id:
            queryset = queryset.filter(episode__brand__id=brand_id)
        brand_slug = self.request.query_params.get("brand_slug", None)
        if brand_slug:
            queryset = queryset.filter(episode__brand__slug=brand_slug)
        station_id = self.request.query_params.get("station_id", None)
        if station_id:
            queryset = queryset.filter(episode__brand__station__station_id=station_id)
        topic = self.request.query_params.get("topic") or self.request.query_params.get("category")
        if topic:
            queryset = queryset.filter(categories__slug=topic)
        # M2M join on categories__name (search) can produce duplicates
        if self.request.query_params.get("search") or topic:
            queryset = queryset.distinct()
        return queryset


def topics_list(request):
    """Return topics with book counts and descriptions."""
    cats = (
        Category.objects.annotate(book_count=Count("book"))
        .filter(book_count__gt=0)
        .order_by("-book_count")
    )
    result = [
        {
            "slug": c.slug,
            "name": c.name,
            "description": c.description,
            "book_count": c.book_count,
        }
        for c in cats
    ]
    return JsonResponse(result, safe=False)


def topic_detail(request, slug):
    """Return a single topic by slug."""
    try:
        cat = Category.objects.annotate(book_count=Count("book")).get(slug=slug)
    except Category.DoesNotExist:
        raise Http404
    return JsonResponse(
        {
            "slug": cat.slug,
            "name": cat.name,
            "description": cat.description,
            "book_count": cat.book_count,
        }
    )


def health_check(request):
    """Health check endpoint — returns 200 if healthy, 503 if not."""
    from .health import get_system_health

    health = get_system_health()
    http_status = 503 if health["status"] == "unhealthy" else 200
    return JsonResponse(health, status=http_status)
