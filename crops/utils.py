from datetime import timedelta
from decimal import Decimal

def calcular_cosecha_costos(sowing):
    cultivo = sowing.product
    fecha_siembra = sowing.sowing_date
    unidad = sowing.area_unit
    area = sowing.area

    estimated_harvest_date = (
        fecha_siembra + timedelta(days=cultivo.cycle_days)
        if cultivo.cycle_days else None
    )

    area_decimal = Decimal(str(area))

    if unidad == 'hectarea' and cultivo.cost_per_hectare:
        estimated_cost = cultivo.cost_per_hectare * area_decimal
    else:
        estimated_cost = None

    return estimated_harvest_date, round(estimated_cost, 2) if estimated_cost else None