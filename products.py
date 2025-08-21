from crops.models import Product, Category
import csv

def cargar_productos_desde_csv(ruta):
    with open(ruta, newline='', encoding='utf-8') as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            nombre_categoria = fila.get('category', '').strip()

            if not nombre_categoria:
                print(f"⚠️ Producto sin categoría: {fila.get('name', 'Sin nombre')}")
                continue

            try:
                categoria = Category.objects.filter(name__iexact=nombre_categoria).first()
                if not categoria:
                    categoria = Category.objects.create(name=nombre_categoria)
                    print(f"🆕 Categoría creada: {categoria.name}")

                producto, creado = Product.objects.update_or_create(
                    name=fila['name'].strip(),
                    defaults={
                        'min_temp': float(fila['min_temp']),
                        'max_temp': float(fila['max_temp']),
                        'min_rain': float(fila['min_rain']),
                        'max_rain': float(fila['max_rain']),
                        'min_humidity': float(fila['min_humidity']),
                        'max_humidity': float(fila['max_humidity']),
                        'min_altitude': int(fila['min_altitude']),
                        'max_altitude': int(fila['max_altitude']),
                        'cycle_days': int(fila['cycle_days']),
                        'cost_per_hectare': int(fila['cost_per_hectare']),
                        'cost_per_fanegada': int(fila['cost_per_fanegada']),
                        'category': categoria
                    }
                )

                print(f"{'✅ Creado' if creado else '🔄 Actualizado'}: {producto.name}")

            except Exception as e:
                print(f"❌ Error con {fila.get('name', 'Sin nombre')}: {e}")