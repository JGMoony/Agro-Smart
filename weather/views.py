import requests
from django.shortcuts import render
from crops.models import Municipality

API_KEY = '8abfc6f9e152b9913e6873d64fa3e4d9'

def weather_view(request):
    context = {}
    if request.method == 'POST':
        municipality_id = request.POST.get('municipality')
        try:
            municipality = Municipality.objects.get(id=municipality_id)
            lat = municipality.latitude
            lon = municipality.longitude

            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&lang=es&appid={API_KEY}"
            response = requests.get(url)
            data = response.json()

            context['municipality'] = municipality.name
            context['temperature'] = data['main']['temp']
            context['humidity'] = data['main']['humidity']
            context['rainfall'] = data.get('rain', {}).get('3h', 0)
            context['description'] = data['weather'][0]['description']

        except Municipality.DoesNotExist:
            context['error'] = "Municipio no encontrado."
        except Exception as e:
            context['error'] = f"Error al consultar clima: {str(e)}"

    context['municipalities'] = Municipality.objects.all()
    return render(request, 'weather.html', context)