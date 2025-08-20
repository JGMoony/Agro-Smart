def calcular_viabilidad(cultivo, clima):
    score = 0
    motivos = []

    if clima['temperature_c'] is not None:
        if cultivo.min_temp <= clima['temperature_c'] <= cultivo.max_temp:
            score += 1
        else:
            motivos.append(f"Temperatura ({clima['temperature_c']}°C) fuera del rango ideal")
    else:
        motivos.append("Temperatura no disponible")

    if clima['rainfall_mm'] is not None:
        if cultivo.min_rain <= clima['rainfall_mm'] <= cultivo.max_rain:
            score += 1
        else:
            motivos.append(f"Lluvia ({clima['rainfall_mm']} mm) fuera del rango ideal")
    else:
        motivos.append("Lluvia no disponible")

    if clima['humidity_pct'] is not None:
        if cultivo.min_humidity <= clima['humidity_pct'] <= cultivo.max_humidity:
            score += 1
        else:
            motivos.append(f"Humedad ({clima['humidity_pct']}%) fuera del rango ideal")
    else:
        motivos.append("Humedad no disponible")

    total_params = 3
    nivel = "baja"
    porcentaje = round((score / total_params) * 100, 2)
    
    if porcentaje >= 70:
        nivel = "alta"
    elif porcentaje >= 50:
        nivel = "media"

    if score > 0 and not motivos:
        motivos = ["Cultivo dentro del rango ideal"]

    return {
        "score": porcentaje,
        "level": nivel,
        "reasons": motivos
    }