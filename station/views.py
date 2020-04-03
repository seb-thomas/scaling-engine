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


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")
