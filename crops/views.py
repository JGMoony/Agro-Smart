from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from datetime import date
from .models import Sowing, Product, Category, Municipality, Prices
from .forms import SowingForm, ViabilityForm, PriceForm, PricePredictForm
from .services import ClimateService, ViabilityEngine, ViabilityResult, calcular_cosecha_costos, calcular_produccion_periodo
from .utils import calcular_cosecha_costos
from weather.utils import get_weather

is_admin = user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')

def home(request):
    return render(request, 'base.html')

@login_required
def dashboard(request):
    sowings = Sowing.objects.filter(
        farmer=request.user
    ).select_related('product__category','municipality')

    produccion_6_meses = calcular_produccion_periodo(request.user)

    return render(request, 'crops/dashboard.html', {
        'sowings': sowings,
        'produccion_6_meses': produccion_6_meses
    })


@login_required
def price_dashboard(request):
    prices = Prices.objects.filter(user=request.user).select_related('product')
    return render(request, 'crops/price_dashboard.html', {'prices': prices})

@login_required
def price_create(request):
    if request.method == 'POST':
        form = PriceForm(request.POST)
        if form.is_valid():
            price = form.save(commit=False)
            price.user = request.user
            price.save()
            
            messages.success(request, 'Precio registrado correctamente')
            return redirect('dashboard')
    else:
        form = PriceForm()
        
    return render(request, 'crops/price_regist.html', {'form': form})

@login_required
def price_edit(request, pk):
    price = get_object_or_404(Prices, pk=pk) 

    if request.method == 'POST':
        form = PriceForm(request.POST, instance=price)
        if form.is_valid():
            form.save()
            messages.success(request, 'Precio actualizado correctamente')
            return redirect('dashboard')
    else:
        form = PriceForm(instance=price)
        
    return render(request, 'crops/price_edit.html', {'form': form, 'price': price})


@login_required
def price_delete(request, pk):
    price = get_object_or_404(Prices, pk=pk)

    if request.method == 'POST':
        price.delete()
        messages.info(request, 'Precio eliminado')
        return redirect('dashboard')

    return render(request, 'crops/price_confirm_delete.html', {'price': price})

@login_required
def price_predit(request):
    predicted_price = None
    UNIT_FACTORS = {
        'k': 1,       # kilo
        'a': 12.5,    # arroba
        't': 1000,    # tonelada
    }
    if request.method =='POST':
        form = PricePredictForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            product = data['product']
            prices = product.prices.all()

            UNIT_FACTORS = {'k': 1, 'a': 12.5, 't': 1000}

            total = 0
            count = 0
            for p in prices:
                factor = UNIT_FACTORS.get(p.unit, 1)
                total += (p.value * p.quantity) / factor
                count += 1

            predicted_price = total / count if count > 0 else None

    else:
        form = PricePredictForm()

    return render(request, 'crops/price_predict.html', {
        'form': form,
        'predicted_price': predicted_price
    })

@login_required
def sowing_create(request):
    if request.method == 'POST':
        form = SowingForm(request.POST)
        if form.is_valid():
            sowing = form.save(commit=False)
            sowing.farmer = request.user

            municipio = sowing.municipality
            fecha_siembra = sowing.sowing_date
            clima = ClimateService.get_conditions(municipio, fecha_siembra)
            viabilidad = ViabilityEngine.evaluate(sowing.product, clima)

            sowing.status = 'ongoing' if viabilidad.level != 'baja' else 'failed'
            sowing.save()

            fecha_cosecha, costo_estimado = calcular_cosecha_costos(sowing)
            sowing.estimated_harvest_date = fecha_cosecha
            sowing.estimated_cost = costo_estimado
            sowing.save(update_fields=['estimated_harvest_date', 'estimated_cost'])

            messages.success(request, 'Siembra registrada correctamente')

            produccion_total = calcular_produccion_periodo(request.user, meses=6)
            messages.info(request, f"Producción estimada próximos 6 meses: {produccion_total:.2f} ha")

            if viabilidad.level == 'baja':
                return render(request, 'crops/sowing_confirm.html', {
                    'form': form,
                    'viabilidad': viabilidad,
                    'sowing': sowing
                })

            return redirect('dashboard')
    else:
        form = SowingForm()

    return render(request, 'crops/sowing_form.html', {'form': form})

@login_required
def sowing_edit(request, pk):
    sowing = get_object_or_404(Sowing, pk=pk, farmer=request.user)
    if request.method == 'POST':
        form = SowingForm(request.POST, instance=sowing)
        if form.is_valid():
            sowing = form.save(commit=False)
            
            sowing.save()
            
            estimated_harvest_date, estimated_cost = calcular_cosecha_costos(sowing)
            sowing.estimated_harvest_date = estimated_harvest_date
            sowing.estimated_cost = estimated_cost
            sowing.save(update_fields=['estimated_harvest_date', 'estimated_cost'])
            
            if estimated_harvest_date:
                messages.info(request, f"Nueva fecha estimada de cosecha: {estimated_harvest_date}")
            if estimated_cost:
                messages.info(request, f"Nuevo costo estimado: ${estimated_cost:,.2f}")
            
            messages.success(request, 'Siembra actualizada correctamente')
            return redirect('dashboard')
    else:
        form = SowingForm(instance=sowing)
        
    return render(request, 'crops/sowing_form.html', {'form': form})

@login_required
def sowing_delete(request, pk):
    sowing = get_object_or_404(Sowing, pk=pk, farmer=request.user)
    if request.method == 'POST':
        sowing.delete()
        messages.info(request, 'Siembra eliminada')
        return redirect('dashboard')
    return render(request, 'crops/sowing_confirm_delete.html', {'sowing': sowing})

@is_admin
def admin_dashboard(request):
    base = Sowing.objects.all()
    total = base.count() or 1
    
    by_product = base.values('product__name').annotate(count=Count('id')).order_by('-count')
    by_category = base.values('product__category__name').annotate(count=Count('id')).order_by('-count')
    by_muni = base.values('municipality__name').annotate(count=Count('id')).order_by('-count')

    to_chart = lambda rows, key: {
        'labels': [r[key] for r in rows],
        'values': [r['count'] for r in rows],
        'percents': [round((r['count']/total)*100, 2) for r in rows]
    }

    context = {
        'chart_product': to_chart(by_product, 'product__name'),
        'chart_category': to_chart(by_category, 'product__category__name'),
        'chart_muni': to_chart(by_muni, 'municipality__name'),
        'total': 0 if base.count()==0 else total,
        'alerts': [
            {
                'type': 'overplanting',
                'message': f"Exceso de {r['product__name']} ({round((r['count']/total)*100,2)}%)",
            }
            for r in by_product if (r['count']/total) >= 0.6
        ]
    }
    return render(request, 'crops/admin_dashboard.html', context)

@login_required
def viability(request):
    result = None
    alternatives = []

    if request.method == 'POST':
        form = ViabilityForm(request.POST)
        if form.is_valid():

            data = form.cleaned_data
            municipality = data['municipality']
            sowing_date = data['sowing_date']
            clima = ClimateService.get_conditions(municipality, sowing_date)

            data['temperature_c'] = clima.get('temperature_c')
            data['rainfall_mm'] = clima.get('rainfall_mm')
            data['humidity_pct'] = clima.get('humidity_pct')
            all_products = Product.objects.all()
            scored = []
            for p in all_products:
                from .services import ViabilityEngine

                result = ViabilityEngine.evaluate(p, data)
                score_dict = {
                    "cultivo": p.name,
                    "score": result.score * 100,
                    "level": result.level,
                    "reasons": result.reasons
                }
                scored.append((p, score_dict['score']))
            scored.sort(key=lambda x: x[1], reverse=True)
            
            for p, s in scored[:3]:
                if s > 0:
                    alternatives.append({
                        'cultivo': p.name,
                        'cycle': p.cycle_days,
                        'temp': f"{p.min_temp} - {p.max_temp} °C",
                        'alt': f"{p.min_altitude} - {p.max_altitude} m",
                        'costo_hectarea': p.cost_per_hectare,
                        'score': s
                    })
    else:
        form = ViabilityForm()
    return render(request, 'crops/viability.html', {
        'form': form,
        'alternatives': alternatives
    })
    
@login_required
def reports_view(request):
    
    sowings = Sowing.objects.filter(farmer=request.user)
    
    total_sowings = sowings.count()
    by_product = sowings.values('product__name').annotate(count=Count('id')).order_by('-count')
    by_municipality = sowings.values('municipality__name').annotate(count=Count('id')).order_by('-count')
    total_cost = sowings.aggregate(total=Sum('estimated_cost'))['total'] or 0
    
    context = {
        'total_sowings': total_sowings,
        'by_product': by_product,
        'total_cost': total_cost
    }
    
    return render(request, 'crops/reports.html', context)

@login_required
def production_view(request):
    farmer = request.user
    municipio_id = request.GET.get('municipio')
    producto_id = request.GET.get('producto')

    municipio = Municipality.objects.get(id=municipio_id) if municipio_id else None
    producto = Product.objects.get(id=producto_id) if producto_id else None

    total_produccion = calcular_produccion_periodo(farmer, meses=6, municipio=municipio, producto=producto)

    context = {
        'total_produccion': total_produccion,
        'municipios': Municipality.objects.all(),
        'productos': Product.objects.all(),
        'selected_municipio': municipio,
        'selected_producto': producto
    }
    return render(request, 'crops/production.html', context)
