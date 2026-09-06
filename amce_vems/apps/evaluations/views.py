import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from apps.core.models import EvaluatorProfile
from apps.vendors.models import Vendor
from apps.schedules.models import MasterCalendar
from apps.forms_builder.models import EvaluationCohort, FormTemplate, CriterionQuestion
from apps.evaluations.models import Submission, EvaluationResponse

@login_required
def active_session_redirect(request):
    """
    Directs the user based on role:
    - Super Admin / Exec -> /executive/
    - Evaluator -> Today's active form or session overview
    """
    if request.user.groups.filter(name__in=['Super Administrator', 'Executive Viewer']).exists():
        return redirect('executive_dashboard')
    return redirect('evaluator_dashboard')

@login_required
def evaluator_dashboard(request):
    """
    Evaluator landing page showing current date, bound vendor, and accessible cohorts.
    """
    profile = getattr(request.user, 'evaluator_profile', None)
    
    # Active calendar date - default to prototype demonstration start date if today is outside demo range
    today = timezone.now().date()
    calendar_slot = MasterCalendar.objects.filter(evaluation_date=today).first()
    if not calendar_slot:
        # Fallback to Day 1 (2026-09-07) for demo/local testing purposes
        calendar_slot = MasterCalendar.objects.first()
    
    cohorts = EvaluationCohort.objects.filter(is_active=True).order_by('cohort_number')
    
    # Check submissions for this evaluator and calendar slot
    submissions_map = {}
    if profile and calendar_slot:
        user_subs = Submission.objects.filter(evaluator=profile, calendar=calendar_slot)
        for sub in user_subs:
            submissions_map[sub.cohort_id] = sub

    context = {
        'profile': profile,
        'calendar_slot': calendar_slot,
        'cohorts': cohorts,
        'submissions_map': submissions_map,
    }
    return render(request, 'evaluations/evaluator_dashboard.html', context)

@login_required
def scorecard_view(request, cohort_slug):
    """
    Interactive Scorecard for an assigned cohort.
    Auto-binds: Evaluator Profile + Today's MasterCalendar Vendor.
    """
    profile = getattr(request.user, 'evaluator_profile', None)
    if not profile:
        messages.error(request, "Your user account has no assigned Evaluator Profile.")
        return redirect('evaluator_dashboard')

    cohort = get_object_or_404(EvaluationCohort, slug=cohort_slug)
    
    # Resolve calendar slot
    today = timezone.now().date()
    calendar_slot = MasterCalendar.objects.filter(evaluation_date=today).first()
    if not calendar_slot:
        calendar_slot = MasterCalendar.objects.first()

    vendor = calendar_slot.vendor
    template = FormTemplate.objects.filter(cohort=cohort).order_by('-version').first()
    if not template:
        messages.error(request, f"No published form template found for {cohort.name}.")
        return redirect('evaluator_dashboard')

    # Determine if demonstration window is locked at calendar or submission level
    calendar_is_locked = calendar_slot.status in ['LOCKED', 'SCHEDULED', 'COMPLETED']
    submission_is_locked = False

    # Get or create active submission draft
    submission_id = f"SUB-{calendar_slot.evaluation_date.strftime('%Y%m%d')}-{cohort.cohort_number:02d}-{profile.id}"
    submission, created = Submission.objects.get_or_create(
        evaluator=profile,
        calendar=calendar_slot,
        cohort=cohort,
        defaults={
            'submission_id': submission_id,
            'vendor': vendor,
            'template': template,
            'status': 'DRAFT'
        }
    )

    if submission.status in ['SUBMITTED', 'MODERATED', 'LOCKED']:
        submission_is_locked = True

    is_locked = calendar_is_locked or submission_is_locked

    # Criteria list and existing responses
    criteria = template.criteria.all().order_by('criterion_number')
    existing_responses = {r.criterion_id: r for r in submission.responses.all()}

    criteria_data = []
    for crit in criteria:
        resp = existing_responses.get(crit.id)
        criteria_data.append({
            'criterion': crit,
            'score': float(resp.score) if resp else 0.0,
            'weighted_score': float(resp.weighted_score) if resp else 0.0,
            'notes': resp.evidence_notes if resp else '',
        })

    context = {
        'profile': profile,
        'cohort': cohort,
        'vendor': vendor,
        'calendar_slot': calendar_slot,
        'submission': submission,
        'criteria_data': criteria_data,
        'is_locked': is_locked,
        'calendar_is_locked': calendar_is_locked,
        'calendar_status': calendar_slot.status,
    }
    return render(request, 'evaluations/scorecard.html', context)

@login_required
def finalize_submission(request, submission_id):
    """
    Final validation check and submission locking.
    Rejects submissions if calendar slot is LOCKED, COMPLETED, or not yet OPEN.
    """
    submission = get_object_or_404(Submission, submission_id=submission_id, evaluator__user=request.user)
    
    # Check Calendar Slot Status
    if submission.calendar.status == 'LOCKED':
        messages.error(request, f"Submission Rejected: The demonstration session for {submission.calendar.day_label} ({submission.vendor.name}) is LOCKED. No new scores or modifications are permitted.")
        return redirect('scorecard_view', cohort_slug=submission.cohort.slug)

    if submission.calendar.status != 'OPEN':
        messages.warning(request, f"Evaluation window is not open. Current status: {submission.calendar.get_status_display()}.")
        return redirect('scorecard_view', cohort_slug=submission.cohort.slug)

    if submission.status in ['SUBMITTED', 'MODERATED', 'LOCKED']:
        messages.info(request, "This scorecard has already been submitted and locked.")
        return redirect('scorecard_view', cohort_slug=submission.cohort.slug)

    # Validate all criteria scored
    template_criteria = submission.template.criteria.all()
    responses = {r.criterion_id: r for r in submission.responses.all()}
    
    missing_criteria = []
    invalid_notes = []
    for crit in template_criteria:
        resp = responses.get(crit.id)
        if not resp or resp.score <= Decimal('0'):
            missing_criteria.append(crit.name)
        elif (resp.score <= Decimal('2.5') or resp.score == Decimal('5.0')) and (not resp.evidence_notes or len(resp.evidence_notes.strip()) < 20):
            invalid_notes.append(f"{crit.name} (Score: {resp.score}) requires minimum 20 characters of evidence notes.")

    if missing_criteria:
        messages.error(request, f"Please complete all criteria before final submission. Missing: {', '.join(missing_criteria[:3])}")
        return redirect('scorecard_view', cohort_slug=submission.cohort.slug)

    if invalid_notes:
        for err in invalid_notes:
            messages.warning(request, err)
        return redirect('scorecard_view', cohort_slug=submission.cohort.slug)

    # Lock submission and generate cryptographic hash
    submission.calculate_total_group_score()
    submission.generate_integrity_hash()
    submission.status = 'SUBMITTED'
    submission.submitted_at = timezone.now()
    submission.save()

    messages.success(request, f"Scorecard for {submission.cohort.name} successfully submitted and locked with integrity seal: {submission.record_hash[:12]}...")
    return redirect('evaluator_dashboard')

