from django.shortcuts import render, redirect
from .models import Siembra
from .models import SiembraForm

def lista_siembras(request):
    siembras = Siembra.objects.all()
    return render(request, "siembras/lista.html", {"siembras": siembras})

def crear_siembra(request):
    if request.method == "POST":
        form = SiembraForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("lista_siembras")
    else:
        form = SiembraForm()
    return render(request, "siembras/crear.html", {"form": form})