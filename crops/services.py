from dataclasses import dataclass
from typing import Dict, List
from .models import Sowing, Product, Municipality

# Rangos ideales simples por cultivo (ajústalos a tu criterio/local)
IDEAL = {
    'Arroz':      {'temp': (22, 30), 'rain': (5, 20), 'hum': (60, 90)},
    'Avena':      {'temp': (10, 20), 'rain': (1, 10), 'hum': (50, 80)},
    'Fresa':      {'temp': (10, 22), 'rain': (1, 8),  'hum': (60, 80)},
    'Tomate':     {'temp': (18, 28), 'rain': (1, 8),  'hum': (40, 70)},
    'Frijoles':   {'temp': (16, 26), 'rain': (3, 12), 'hum': (50, 80)},
    'Lenteja':    {'temp': (10, 20), 'rain': (1, 8),  'hum': (40, 70)},
}

@dataclass
class ViabilityResult:
    level: str
    score: float
    reasons: List[str]
    alternatives: List[str]

class ClimateService:
    """
    Servicio simple: si no recibes parámetros climáticos manuales,
    pone valores neutros. Puedes reemplazar por una llamada a API.
    """
    @staticmethod
    def get_conditions(municipality: Municipality, sowing_date, overrides=None):
        if overrides:
            return overrides
        # Valores base neutros
        return {'temperature_c': 20.0, 'rainfall_mm': 3.0, 'humidity_pct': 70.0}

class ViabilityEngine:
    @staticmethod
    def _range_score(value, r):
        lo, hi = r
        if value < lo:  # penaliza distancia
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

        # Producción existente (saturación por share del producto en el municipio)
        base = Sowing.objects.filter(municipality=municipality)
        total = base.count() or 1
        share = base.filter(product=product).count() / total
        # Penaliza si supera 60% del total en esa zona
        saturation_penalty = 0.2 if share >= 0.6 else 0.0
        if saturation_penalty:
            reasons.append(f"Saturación local de {name}: {round(share*100,1)}%")

        t = conditions['temperature_c']
        r = conditions['rainfall_mm']
        h = conditions['humidity_pct']

        t_score = cls._range_score(t, ideal['temp'])
        r_score = cls._range_score(r, ideal['rain'])
        h_score = cls._range_score(h, ideal['hum'])

        score = max(0.0, (t_score + r_score + h_score)/3 - saturation_penalty)

        if score >= 0.75:
            level = 'alta'
        elif score >= 0.45:
            level = 'media'
        else:
            level = 'baja'

        if level == 'baja':
            # Recomienda 3 alternativas con mejor puntaje (mismo municipio, mismas condiciones)
            alts = []
            for p in Product.objects.exclude(id=product.id):
                ideal_p = IDEAL.get(p.name)
                if not ideal_p:
                    continue
                s = (
                    cls._range_score(t, ideal_p['temp']) +
                    cls._range_score(r, ideal_p['rain']) +
                    cls._range_score(h, ideal_p['hum'])
                )/3
                alts.sort(key=lambda x: x[1], reverse=True)
                alts.append((p.name, s))
            alts.sort(key=lambda x: x[1], reverse=True)
            alternatives = [name for name, _ in alts[:3]]
        else:
            alternatives = []

        # Motivos climáticos
        def _msg(v, r, label):
            lo, hi = r
            if v < lo:
                return f"{label} por debajo del ideal ({v} < {lo})"
            if v > hi:
                return f"{label} por encima del ideal ({v} > {hi})"
            return f"{label} dentro del ideal ({lo}-{hi})"

        reasons.extend([
            _msg(t, ideal['temp'], 'Temperatura'),
            _msg(r, ideal['rain'], 'Lluvia'),
            _msg(h, ideal['hum'], 'Humedad'),
        ])

        return ViabilityResult(level, round(score, 2), reasons, alternatives)