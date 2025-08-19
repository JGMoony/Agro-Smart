import requests
from django.conf import settings

def get_weather(lat, lon):
    api_key = settings.OPENWEATHER_API_KEY
    url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&lang=es&appid={api_key}'
    response = requests.get(url)

    try:
        data = response.json()
        print("Respuesta de OpenWeatherMap:", data)
        
    except Exception as e:
        print("Error al decodificar JSON:", e)
        return {'error': 'Respuesta inválida del servidor climático'}

    if response.status_code != 200 or 'main' not in data:
        return {'error': data.get('mesagge', 'No se pudo obtener datos climáticos válidos')}

    return {
        'temperatura': data['main']['temp'],
        'descripcion': data['weather'][0]['description'],
        'humedad': data['main']['humidity'],
        'viento': data['wind']['speed']
    }
    
def get_coordinates(municipio_name):
    url = 'https://nominatim.openstreetmap.org/search'
    params = {
        'q': f'{municipio_name}, Colombia',
        'format': 'json',
        'limit': 1
    }
    headers = {
        'User-Agent': 'TuProyectoAgricola/1.0 (tu-email@example.com)'  # Requerido por Nominatim
    }

    response = requests.get(url, params=params, headers=headers)
    data = response.json()

    if data:
        return {
            'latitude': float(data[0]['lat']),
            'longitude': float(data[0]['lon'])
        }
    return None