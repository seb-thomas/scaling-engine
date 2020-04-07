from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from rest_framework import viewsets

from .serializers import StationSerializer
from .models import Station


class StationView(viewsets.ModelViewSet):
    serializer_class = StationSerializer
    queryset = Station.objects.all()


def index(request):
    station_list = Station.objects.all()[:5]
    context = {
        "station_list": station_list,
    }
    return render(request, "stations/index.html", context)


def detail(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    return render(request, "stations/detail.html", {"station": station})
