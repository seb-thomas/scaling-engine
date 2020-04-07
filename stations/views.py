from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from .models import Station


def index(request):
    station_list = Station.objects.all()[:5]
    context = {
        "station_list": station_list,
    }
    return render(request, "stations/index.html", context)


def detail(request, station_id):
    station = get_object_or_404(Station, pk=station_id)
    return render(request, "stations/detail.html", {"station": station})
