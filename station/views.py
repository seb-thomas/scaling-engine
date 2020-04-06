# from django.shortcuts import render, redirect
# from .models import Station
# from .forms import StationModelForm

# # Create your views here.
# def create_view(request):
#     form = StationModelForm(request.POST or None)
#     if form.is_valid():
#         form.save()
#         return redirect("/")

#     context = {"form": form}

#     return render(request, "station/create.html", context)
from django.http import HttpResponse
from .models import Station


def index(request):
    latest_question_list = Station.objects.all()[:5]
    output = ", ".join([q.name for q in latest_question_list])
    return HttpResponse(output)


def detail(request, station_id):
    return HttpResponse("Youre looking at %s. " % station_id)
