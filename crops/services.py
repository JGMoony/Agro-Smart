from dataclasses import dataclass
from typing import Dict, List
from .models import Sowing, Product, Municipality
import requests
from django.conf import settings
from datetime import timedelta

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

@dataclass
class ViabilityResult:
    level: str
    score: float
    reasons: List[str]
    alternatives: List[Dict]  
    
class ViabilityEngine:
    @staticmethod
    def _range_score(value, r_min, r_max):
        if value is None or r_min is None or r_max is None:
            return 0.0
        if value < r_min:
            return max(0, 1 - (r_min - value) / max(1, (r_max - r_min)))
        if value > r_max:
            return max(0, 1 - (value - r_max) / max(1, (r_max - r_min)))
        return 1.0

    @classmethod
    def evaluate(cls, product: Product, conditions: Dict) -> ViabilityResult:
        t = conditions.get('temperature_c')
        r = conditions.get('rainfall_mm')
        h = conditions.get('humidity_pct')

        t_score = cls._range_score(t, product.min_temp, product.max_temp)
        r_score = cls._range_score(r, product.min_rain, product.max_rain)
        h_score = cls._range_score(h, product.min_humidity, product.max_humidity)

        score = round((t_score + r_score + h_score) / 3, 2)
        level = 'alta' if score >= 0.75 else 'media' if score >= 0.45 else 'baja'

        def _msg(v, lo, hi, label):
            if v is None or lo is None or hi is None:
                return f"{label} no disponible"
            if v < lo:
                return f"{label} por debajo del ideal ({v} < {lo})"
            if v > hi:
                return f"{label} por encima del ideal ({v} > {hi})"
            return f"{label} dentro del ideal ({lo}–{hi})"

        reasons = [
            _msg(t, product.min_temp, product.max_temp, 'Temperatura'),
            _msg(r, product.min_rain, product.max_rain, 'Lluvia'),
            _msg(h, product.min_humidity, product.max_humidity, 'Humedad'),
        ]

        alternatives = cls.recommend(product, conditions)
        return ViabilityResult(level, score, reasons, alternatives)

    @classmethod
    def recommend(cls, excluded_product: Product, conditions: Dict) -> List[Dict]:
        t = conditions.get('temperature_c')
        r = conditions.get('rainfall_mm')
        h = conditions.get('humidity_pct')
        candidates = []

        for p in Product.objects.exclude(id=excluded_product.id):
            score = (
                cls._range_score(t, p.min_temp, p.max_temp) +
                cls._range_score(r, p.min_rain, p.max_rain) +
                cls._range_score(h, p.min_humidity, p.max_humidity)
            ) / 3

            candidates.append({
                'cultivo': p.name,
                'score': round(score, 2),
                'cycle': p.cycle_days,
                'temp': f"{p.min_temp}–{p.max_temp} °C" if p.min_temp and p.max_temp else "N/D",
                'alt': f"{p.min_altitude}–{p.max_altitude} m" if p.min_altitude and p.max_altitude else "N/D",
                'costo_hectarea': p.cost_per_hectare or 0,
                'costo_fanegada': p.cost_per_fanegada or 0,
            })

        return sorted(candidates, key=lambda x: x['score'], reverse=True)[:3]
        
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

def top3_cultivos(data):
    cultivos = Product.objects.all()
    resultados = []

    for p in cultivos:
        result = ViabilityEngine.evaluate(p, data)
        resultados.append({
            "cultivo": p.name,
            "score": result.score * 100,
            "level": result.level,
            "reasons": result.reasons,
            "cycle": p.cycle_days,
            "temp": f"{p.min_temp}–{p.max_temp} °C" if p.min_temp and p.max_temp else "N/D",
            "alt": f"{p.min_altitude}–{p.max_altitude} m" if p.min_altitude and p.max_altitude else "N/D",
            "costo_hectarea": p.cost_per_hectare or 0,
            "value": p.id
        })

    return sorted(resultados, key=lambda x: x['score'], reverse=True)[:3]

def calcular_cosecha_costos(sowing: Sowing):
    cultivo = sowing.product
    fecha = sowing.sowing_date
    unidad = sowing.unit
    cantidad = sowing.quantity

    fecha_cosecha = fecha + timedelta(days=cultivo.cycle_days) if cultivo.cycle_days else None

    if unidad == 'hectarea' and cultivo.cost_per_hectare:
        costo = cultivo.cost_per_hectare * cantidad
    elif unidad == 'fanegada' and cultivo.cost_per_fanegada:
        costo = cultivo.cost_per_fanegada * cantidad
    else:
        costo = None

    return fecha_cosecha, costo