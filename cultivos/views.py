from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum
from .models import Category, Product, Municipality, Sowing
from .serializers import CategorySerializer, ProductSerializer, MunicipalitySerializer, SowingSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

class MunicipalityViewSet(viewsets.ModelViewSet):
    queryset = Municipality.objects.all()
    serializer_class = MunicipalitySerializer
    permission_classes = [permissions.IsAuthenticated]

class SowingViewSet(viewsets.ModelViewSet):
    queryset = Sowing.objects.select_related('farmer', 'product__category', 'municipality').all()
    serializer_class = SowingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.role == 'farmer':
            qs = qs.filter(farmer=user)
        # Filtros opcionales por query params
        product_id = self.request.query_params.get('product')
        municipality_id = self.request.query_params.get('municipality')
        if product_id:
            qs = qs.filter(product_id=product_id)
        if municipality_id:
            qs = qs.filter(municipality_id=municipality_id)
        return qs

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAdminUser])
    def stats(self, request):
        """
        Estadísticas para el panel del administrador:
        - Conteo total
        - Distribución por producto/categoría/municipio (porcentajes)
        - Alerta por exceso de siembra (no plagas): si un producto supera umbral en % del total
        Query params: threshold (0-1), municipality (id opcional)
        """
        threshold = float(request.query_params.get('threshold', 0.6))
        municipality = request.query_params.get('municipality')
        base = self.get_queryset()
        if municipality:
            base = base.filter(municipality_id=municipality)

        total = base.count() or 1

        by_product = (
            base.values('product__id', 'product__name')
                .annotate(count=Count('id'))
                .order_by('-count')
        )
        by_category = (
            base.values('product__category__id', 'product__category__name')
                .annotate(count=Count('id'))
                .order_by('-count')
        )
        by_muni = (
            base.values('municipality__id', 'municipality__name')
                .annotate(count=Count('id'))
                .order_by('-count')
        )

        def to_percent(rows, name_key):
            return [
                {
                    'name': r[name_key],
                    'count': r['count'],
                    'percent': round((r['count'] / total) * 100, 2)
                }
                for r in rows
            ]

        prod_percent = to_percent(by_product, 'product__name')
        cat_percent = to_percent(by_category, 'product__category__name')
        muni_percent = to_percent(by_muni, 'municipality__name')

        # Alertas por exceso de siembra (no plagas)
        alerts = [
            {
                'type': 'overplanting',
                'message': f"Exceso de {r['product__name']} ({round((r['count']/total)*100,2)}%)",
            }
            for r in by_product
            if (r['count'] / total) >= threshold
        ]

        return Response({
            'total_sowings': total if total != 1 else (0 if base.count() == 0 else total),
            'by_product': prod_percent,
            'by_category': cat_percent,
            'by_municipality': muni_percent,
            'alerts': alerts,
        })