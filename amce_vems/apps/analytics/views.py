import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from apps.analytics.services import ScoringEngineService
from apps.forms_builder.models import EvaluationCohort
from apps.vendors.models import Vendor

def can_access_executive_dashboard(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff or user.groups.filter(name__in=['Super Administrator', 'Executive Viewer']).exists():
        return True
    return user.has_perm('analytics.can_view_executive_dashboard')

@login_required
@user_passes_test(can_access_executive_dashboard)
def executive_dashboard_view(request):

    """
    Renders the live Executive Scorecard:
    - 5-Vendor vs 7-Cohort Performance Matrix
    - Overall Weighted Scores & Ranks
    - Radar Comparison Data
    """
    matrix_data = ScoringEngineService.generate_executive_scorecard_matrix()
    cohorts = EvaluationCohort.objects.filter(is_active=True).order_by('cohort_number')
    vendors = Vendor.objects.filter(is_active=True)

    # Prepare datasets for Radar Chart
    cohort_labels = [c.name for c in cohorts]
    radar_datasets = []
    
    palette = [
        {'border': 'rgba(11, 37, 69, 1)', 'bg': 'rgba(11, 37, 69, 0.2)'},     # Navy (ezCareTech)
        {'border': 'rgba(19, 154, 140, 1)', 'bg': 'rgba(19, 154, 140, 0.2)'},  # Teal (ESI)
        {'border': 'rgba(217, 119, 6, 1)', 'bg': 'rgba(217, 119, 6, 0.2)'},    # Amber (SRIT)
        {'border': 'rgba(5, 150, 105, 1)', 'bg': 'rgba(5, 150, 105, 0.2)'},    # Green (MEDITECH)
        {'border': 'rgba(220, 38, 38, 1)', 'bg': 'rgba(220, 38, 38, 0.2)'},    # Crimson (KRANIUM)
    ]

    for idx, v_res in enumerate(matrix_data):
        scores = [v_res['breakdown'].get(c.slug, {}).get('raw_score', 0) for c in cohorts]
        color = palette[idx % len(palette)]
        radar_datasets.append({
            'label': v_res['vendor_name'],
            'data': scores,
            'borderColor': color['border'],
            'backgroundColor': color['bg'],
            'borderWidth': 2
        })

    context = {
        'matrix_data': matrix_data,
        'cohorts': cohorts,
        'vendors': vendors,
        'radar_labels_json': json.dumps(cohort_labels),
        'radar_datasets_json': json.dumps(radar_datasets),
    }
    return render(request, 'executive/dashboard.html', context)

@login_required
@user_passes_test(can_access_executive_dashboard)
def sensitivity_simulator_api(request):

    """
    Simulates alternate cohort weights on-the-fly without database modification.
    """
    try:
        custom_weights = json.loads(request.body)
        simulated_matrix = ScoringEngineService.generate_executive_scorecard_matrix(custom_weights)
        return JsonResponse({'status': 'success', 'matrix': simulated_matrix})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
