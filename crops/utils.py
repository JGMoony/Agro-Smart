from datetime import timedelta, date

def calcular_viabilidad(cultivo, clima, sowing_date=None):
    """
    Calcula la viabilidad de un cultivo según las condiciones climáticas.
    Devuelve score, nivel, motivos y datos adicionales: ciclo, costo, altitud y fecha estimada de cosecha.
    """
    score = 0
    motivos = []

    t = clima.get('temperature_c')
    if t is not None and cultivo.min_temp is not None and cultivo.max_temp is not None:
        if cultivo.min_temp <= t <= cultivo.max_temp:
            score += 1
        else:
            motivos.append(f"Temperatura ({t}°C) fuera del rango ideal ({cultivo.min_temp}-{cultivo.max_temp}°C)")
    else:
        motivos.append("Temperatura no disponible")

    r = clima.get('rainfall_mm')
    if r is not None and cultivo.min_rain is not None and cultivo.max_rain is not None:
        if cultivo.min_rain <= r <= cultivo.max_rain:
            score += 1
        else:
            motivos.append(f"Lluvia ({r} mm) fuera del rango ideal ({cultivo.min_rain}-{cultivo.max_rain} mm)")
    else:
        motivos.append("Lluvia no disponible")

    h = clima.get('humidity_pct')
    if h is not None and cultivo.min_humidity is not None and cultivo.max_humidity is not None:
        if cultivo.min_humidity <= h <= cultivo.max_humidity:
            score += 1
        else:
            motivos.append(f"Humedad ({h}%) fuera del rango ideal ({cultivo.min_humidity}-{cultivo.max_humidity}%)")
    else:
        motivos.append("Humedad no disponible")

    total_params = 3
    porcentaje = round((score / total_params) * 100, 2)
    nivel = "baja"
    if porcentaje >= 70:
        nivel = "alta"
    elif porcentaje >= 50:
        nivel = "media"

    if score > 0 and not motivos:
        motivos = ["Cultivo dentro del rango ideal"]

    if sowing_date and cultivo.cycle_days:
        estimated_harvest_date = sowing_date + timedelta(days=cultivo.cycle_days)
    else:
        estimated_harvest_date = None

    return {
        "score": porcentaje,
        "level": nivel,
        "reasons": motivos,
        "cycle_days": cultivo.cycle_days,
        "estimated_harvest_date": estimated_harvest_date,
        "cost_per_hectare": cultivo.cost_per_hectare,
        "cost_per_fanegada": cultivo.cost_per_fanegada,
        "min_altitude": cultivo.min_altitude,
        "max_altitude": cultivo.max_altitude
    }

    
def calcular_cosecha_costos(sowing):
    cultivo = sowing.product
    estimated_harvest_date = None
    estimated_cost = None

    if cultivo.cycle_days:
        estimated_harvest_date = sowing.sowing_date + timedelta(days=cultivo.cycle_days)

    if sowing.unit == 'hectarea' and cultivo.cost_per_hectare:
        estimated_cost = cultivo.cost_per_hectare * sowing.quantity
    elif sowing.unit == 'fanegada' and cultivo.cost_per_fanegada:
        estimated_cost = cultivo.cost_per_fanegada * sowing.quantity

    sowing.estimated_harvest_data = estimated_harvest_date
    sowing.estimated_cost = estimated_cost
    
    return estimated_harvest_date, estimated_cost