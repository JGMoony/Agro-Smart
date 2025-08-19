from django.core.management.base import BaseCommand
from crops.models import Municipality
from weather.utils import get_coordinates

class Command(BaseCommand):
    help = 'Actualiza coordenadas de municipios usando Nominatim'

    def handle(self, *args, **kwargs):
        municipios = Municipality.objects.filter(latitude__isnull=True, longitude__isnull=True)

        for municipio in municipios:
            coords = get_coordinates(municipio.name)
            if coords:
                municipio.latitude = coords['latitude']
                municipio.longitude = coords['longitude']
                municipio.save()
                self.stdout.write(self.style.SUCCESS(f'✔ Coordenadas actualizadas para {municipio.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠ No se encontraron coordenadas para {municipio.name}'))