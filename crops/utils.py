from datetime import timedelta

def calcular_cosecha_costos(sowing):
    cultivo = sowing.product
    fecha_siembra = sowing.sowing_date
    unidad = sowing.unit
    cantidad = sowing.quantity

    estimated_harvest_date = fecha_siembra + timedelta(days=cultivo.cycle_days) if cultivo.cycle_days else None

    if unidad == 'hectarea' and cultivo.cost_per_hectare:
        estimated_cost = cultivo.cost_per_hectare * cantidad
    elif unidad == 'fanegada' and cultivo.cost_per_fanegada:
        estimated_cost = cultivo.cost_per_fanegada * cantidad
    else:
        estimated_cost = None

    return estimated_harvest_date, estimated_cost