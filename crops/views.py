from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from .models import Sowing, Product, Category, Municipality
from .forms import SowingForm, ViabilityForm
from .services import ClimateService, ViabilityEngine

# Helper para rol admin
is_admin = user_passes_test(lambda u: u.is_authenticated and u.role == 'admin')

@login_required
def dashboard(request):
    # Panel del agricultor (sus siembras)
    sowings = Sowing.objects.filter(farmer=request.user).select_related('product__category','municipality')
    return render(request, 'crops/dashboard.html', {'sowings': sowings})

@login_required
def sowing_create(request):
    if request.method == 'POST':
        form = SowingForm(request.POST)
        if form.is_valid():
            sowing = form.save(commit=False)
            sowing.farmer = request.user
            sowing.save()
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
            form.save()
            messages.success(request, 'Siembra actualizada')
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
    if request.method == 'POST':
        form = ViabilityForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            municipality = form.cleaned_data['municipality']
            sowing_date = form.cleaned_data['sowing_date']
            overrides = {
                k: form.cleaned_data[k] for k in ['temperature_c','rainfall_mm','humidity_pct']
                if form.cleaned_data.get(k) is not None
            }
            conditions = ClimateService.get_conditions(municipality, sowing_date, overrides or None)
            result = ViabilityEngine.evaluate(product, municipality, sowing_date, conditions)
    else:
        form = ViabilityForm()
    return render(request, 'crops/viability.html', {'form': form, 'result': result})