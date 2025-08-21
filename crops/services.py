from dataclasses import dataclass
from typing import Dict, List
from .models import Sowing, Product, Municipality
import requests
from django.conf import settings
from datetime import timedelta

IDEAL = {
    'Fresa':            {'temp': (15, 24), 'rain': (50, 150), 'hum': (70, 90)},
    'Mora':             {'temp': (16, 25), 'rain': (60, 150), 'hum': (65, 85)},
    'Tomate de árbol':  {'temp': (14, 24), 'rain': (40, 120), 'hum': (60, 80)},
    'Uchuva':           {'temp': (12, 22), 'rain': (60, 180), 'hum': (65, 85)},
    'Curuba':           {'temp': (12, 22), 'rain': (60, 180), 'hum': (65, 85)},
    'Papa':             {'temp': (10, 20), 'rain': (60, 120), 'hum': (70, 90)},
    'Zanahoria':        {'temp': (12, 20), 'rain': (50, 100), 'hum': (60, 80)},
    'Cebolla':          {'temp': (12, 24), 'rain': (40, 100), 'hum': (60, 80)},
    'Repollo':          {'temp': (12, 20), 'rain': (50, 120), 'hum': (65, 85)},
    'Habichuela':       {'temp': (18, 28), 'rain': (60, 120), 'hum': (60, 80)},
    'Lechuga':          {'temp': (12, 22), 'rain': (50, 120), 'hum': (65, 85)},
    'Acelga':           {'temp': (12, 22), 'rain': (50, 120), 'hum': (60, 85)},
    'Espinaca':         {'temp': (10, 20), 'rain': (50, 120), 'hum': (60, 85)},
    'Remolacha':        {'temp': (12, 22), 'rain': (50, 120), 'hum': (60, 85)},
    'Maíz':             {'temp': (18, 28), 'rain': (70, 150), 'hum': (60, 85)},
    'Fríjol':           {'temp': (15, 25), 'rain': (50, 120), 'hum': (55, 80)},
    'Lentejas':         {'temp': (15, 22), 'rain': (40, 100), 'hum': (50, 75)},
    'Arveja':           {'temp': (10, 20), 'rain': (40, 100), 'hum': (55, 80)},
}

@dataclass
class ViabilityResult:
    level: str
    score: float
    reasons: List[str]
    alternatives: List[str]

class ClimateService:
    @staticmethod
    def get_conditions(municipality: Municipality, sowing_date) -> Dict:
        lat = municipality.latitude
        lon = municipality.longitude
        api_key = settings.OPENWEATHER_API_KEY

        url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units=metric&lang=es&appid={api_key}'
        response = requests.get(url)
        data = response.json()

        return {
            'temperature_c': data['main']['temp'],
            'humidity_pct': data['main']['humidity'],
            'rainfall_mm': data.get('rain', {}).get('1h', 0),
        }

class ViabilityEngine:
    @staticmethod
    def _range_score(value, r):
        if value is None or r is None:
            return 0.0
        
        lo, hi = r
        if value < lo:
            return max(0, 1 - (lo - value) / max(1, (hi - lo)))
        if value > hi:
            return max(0, 1 - (value - hi) / max(1, (hi - lo)))
        return 1.0

    @classmethod
    def evaluate(cls, product: Product, municipality: Municipality, sowing_date, conditions: Dict) -> ViabilityResult:
        name = product.name
        ideal = IDEAL.get(name)
        reasons = []
        if not ideal:
            return ViabilityResult('media', 0.5, ['Cultivo sin parámetros definidos'], [])

        t = conditions['temperature_c']
        r = conditions['rainfall_mm']
        h = conditions['humidity_pct']

        t_score = cls._range_score(t, ideal['temp'])
        r_score = cls._range_score(r, ideal['rain'])
        h_score = cls._range_score(h, ideal['hum'])

        score = (t_score + r_score + h_score)/3

        if score >= 0.75:
            level = 'alta'
        elif score >= 0.45:
            level = 'media'
        else:
            level = 'baja'

        reasons = []
        def _msg(v, r, label):
            if v is None:
                return f"{label} no disponible"
            lo, hi = r
            if v < lo:
                return f"{label} por debajo del ideal ({v} < {lo})"
            if v > hi:
                return f"{label} por encima del ideal ({v} > {hi})"
            return f"{label} dentro del ideal ({lo}-{hi})"

        reasons.extend([
            _msg(t, ideal.get('temp'), 'Temperatura'),
            _msg(r, ideal.get('rain'), 'Lluvia'),
            _msg(h, ideal.get('hum'), 'Humedad'),
        ])
        alts = []
        for p in Product.objects.exclude(id=product.id):
            ideal_p = IDEAL.get(p.name)
            if not ideal_p:
                continue
            s = (cls._range_score(t, ideal_p.get('temp')) +
                cls._range_score(r, ideal_p.get('rain')) +
                cls._range_score(h, ideal_p.get('hum'))) / 3
            alts.append((p.name, s))
        alts.sort(key=lambda x: x[1], reverse=True)
        alternatives = [name for name, _ in alts[:3]]

        return ViabilityResult(level, round(score,2), reasons, alternatives)    
    
def calcular_viabilidad(cultivo, clima):
    score = 0
    motivos = []

    t = clima.get('temperature_c')
    r = clima.get('rainfall_mm')
    h = clima.get('humidity_pct')

    if t is not None and cultivo.min_temp is not None and cultivo.max_temp is not None:
        if cultivo.min_temp <= t <= cultivo.max_temp:
            score += 1
        else:
            motivos.append(f"Temperatura ({t}°C) fuera del rango ideal ({cultivo.min_temp}-{cultivo.max_temp}°C)")
    else:
        motivos.append("Temperatura no disponible")

    if r is not None and cultivo.min_rain is not None and cultivo.max_rain is not None:
        if cultivo.min_rain <= r <= cultivo.max_rain:
            score += 1
        else:
            motivos.append(f"Lluvia ({r} mm) fuera del rango ideal ({cultivo.min_rain}-{cultivo.max_rain} mm)")
    else:
        motivos.append("Lluvia no disponible")

    if h is not None and cultivo.min_humidity is not None and cultivo.max_humidity is not None:
        if cultivo.min_humidity <= h <= cultivo.max_humidity:
            score += 1
        else:
            motivos.append(f"Humedad ({h}%) fuera del rango ideal ({cultivo.min_humidity}-{cultivo.max_humidity}%)")
    else:
        motivos.append("Humedad no disponible")

    total_params = 3
    porcentaje = round((score / total_params) * 100, 2)

    if porcentaje >= 70:
        nivel = "alta"
    elif porcentaje >= 50:
        nivel = "media"
    else:
        nivel = "baja"

    if score > 0 and not motivos:
        motivos = ["Cultivo dentro del rango ideal"]

    return {
        "cultivo": cultivo.name,
        "score": porcentaje,
        "level": nivel,
        "reasons": motivos
    }

def top3_cultivos(clima):
    cultivos = Product.objects.all()
    resultados = [calcular_viabilidad(c, clima) for c in cultivos]
    resultados_sorted = sorted(resultados, key=lambda x: x['score'], reverse=True)
    return resultados_sorted[:3]

def calcular_cosecha_costos(sowing):
    cultivo = sowing.product
    estimated_harvest_date = None
    estimated_cost = None
    
    if cultivo.cycle_days and sowing.sowing_date:
        sowing.estimated_harvest_date = sowing.sowing_date + timedelta(days=cultivo.cycle_days)
        
    if sowing.unit == 'hectarea' and cultivo.cost_per_hectare:
        sowing.estimated_cost = cultivo.cost_per_hectare * sowing.quantity
    elif sowing.unit == 'fanegada' and cultivo.cost_per_fanegada:
        sowing.estimated_cost = cultivo.cost_per_fanegada * sowing.quantity
    else:
        sowing.estimated_cost = None
        
    sowing.save(update_fields=['estimated_harvest_date', 'estimated_cost'])
    
    return {
        "sowing": sowing,
        "estimated_harvest_date": sowing.estimated_harvest_date,
        "estimated_cost": sowing.estimated_cost
    }