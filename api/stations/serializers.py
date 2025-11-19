from rest_framework import serializers
from .models import Station, Book, Episode, Brand


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = ('id', 'name', 'station_id', 'url', 'created')


class BrandShowSerializer(serializers.ModelSerializer):
    station = StationSerializer(read_only=True)
    book_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = ('id', 'name', 'description', 'url', 'station', 'book_count')
    
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
    brand = BrandShowSerializer(read_only=True)
    
    class Meta:
        model = Episode
        fields = ('id', 'title', 'url', 'description', 'aired_at', 'has_book', 'brand')


class BookSerializer(serializers.ModelSerializer):
    episode = EpisodeSerializer(read_only=True)
    
    class Meta:
        model = Book
        fields = ('id', 'title', 'author', 'description', 'cover_image', 'episode')
