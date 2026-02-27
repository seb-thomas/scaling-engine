from rest_framework import serializers
from .models import Station, Book, Episode, Brand, Category


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ('id', 'name', 'station_id', 'url', 'description', 'created')


class BrandShowSerializer(serializers.ModelSerializer):
    station = StationSerializer(read_only=True)
    book_count = serializers.SerializerMethodField()

    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'description', 'url', 'station', 'book_count', 'brand_color', 'producer_name', 'producer_url')
    
    def get_book_count(self, obj):
        # Use annotated_book_count if available (from queryset annotation)
        if hasattr(obj, 'annotated_book_count'):
            return obj.annotated_book_count or 0
        # Fallback: use the property
        try:
            return obj.book_count
        except:
            return 0


class EpisodeSerializer(serializers.ModelSerializer):
    """Public API: do not add scraped_data, extraction_result, last_error, task_id."""

    brand = BrandShowSerializer(read_only=True)

    class Meta:
        model = Episode
        fields = ('id', 'title', 'url', 'slug', 'aired_at', 'has_book', 'brand')


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('slug', 'name', 'description')


class BookSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    cover_image = serializers.SerializerMethodField()
    categories = CategorySerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = ('id', 'title', 'slug', 'author', 'categories', 'description', 'cover_image', 'purchase_link', 'episodes')

    def get_cover_image(self, obj):
        """Return cover image URL if available"""
        if obj.cover_image:
            return obj.cover_image.url
        return ""
