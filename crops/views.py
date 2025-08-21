from django.utils import timezone
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count, Sum
from datetime import date
from .models import Sowing, Product, Category, Municipality
from .forms import SowingForm, ViabilityForm
from .services import ClimateService, ViabilityEngine, ViabilityResult, calcular_cosecha_costos
from .utils import calcular_viabilidad, calcular_cosecha_costos
from weather.utils import get_weather

is_admin = user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')

def home(request):
    return render(request, 'base.html')

@login_required
def dashboard(request):
    sowings = Sowing.objects.filter(farmer=request.user).select_related('product__category','municipality')
    return render(request, 'crops/dashboard.html', {'sowings': sowings})

@login_required
def sowing_create(request):
    if request.method == 'POST':
        form = SowingForm(request.POST)
        if form.is_valid():
            sowing = form.save(commit=False)
            sowing.farmer = request.user
            
            municipio = sowing.municipality
            if municipio.latitude and municipio.longitude:
                clima = get_weather(municipio.latitude, municipio.longitude)
            else:
                clima = None
                
            sowing.save()
                
            estimated_harvest_date, estimated_cost = calcular_cosecha_costos(sowing)
            sowing.save()
            sowing.estimated_harvest_date = estimated_harvest_date
            sowing.estimated_cost = estimated_cost
            sowing.save(update_fields=['estimated_harvest_date', 'estimated_cost'])
            
            if estimated_harvest_date:
                messages.info(request, f"Fecha estimada de cosecha: {estimated_harvest_date}")
            if estimated_cost:
                messages.info(request, f"Costo estimado: ${estimated_cost:,.2f}")
            
            messages.success(request, 'Siembra registrada correctamente')
            
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
            product = data['product']
            municipality = data['municipality']
            sowing_date = data['sowing_date']

            clima = ClimateService.get_conditions(municipality, sowing_date)
            print("Clima API:", clima)

            data['temperature_c'] = clima.get('temperature_c')
            data['rainfall_mm'] = clima.get('rainfall_mm')
            data['humidity_pct'] = clima.get('humidity_pct')

            result = calcular_viabilidad(product, data, sowing_date=sowing_date)

            if result['level'] in ['baja', 'media']:
                all_products = Product.objects.all()
                scored = []
                for p in all_products:
                    score_dict = calcular_viabilidad(p, data, sowing_date=sowing_date)
                    scored.append((p, score_dict['score'], score_dict))
                scored.sort(key=lambda x: x[1], reverse=True)
                
                for p, s, score_dict in scored[:3]:
                    if s > 0:
                        alternatives.append({
                            'cultivo': p.name,
                            'cycle_days': score_dict['cycle_days'],
                            'estimated_harvest_date': score_dict['estimated_harvest_date'],
                            'altitude_range': f"{score_dict['min_altitude']} - {score_dict['max_altitude']} m",
                            'cost_per_hectare': score_dict['cost_per_hectare'],
                            'cost_per_fanegada': score_dict['cost_per_fanegada'],
                            'score': s
                        })

    else:
        form = ViabilityForm()

    return render(request, 'crops/viability.html', {
        'form': form,
        'result': result,
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