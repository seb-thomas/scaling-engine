
from rest_framework import serializers
from .models import Station

class TodoSerializer(serializers.ModelSerializer):
    class meta:
        model = Station
        fields = ('name', 'url')