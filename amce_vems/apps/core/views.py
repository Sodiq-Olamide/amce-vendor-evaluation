from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.db.models import Q
from apps.core.models import Department, EvaluatorProfile, EmailMessageTemplate, EmailNotificationLog
from apps.core.forms import (
    UserRoleAdminCreationForm, UserRoleAdminChangeForm, UserFromADProvisionForm,
    EmailMessageTemplateForm, EmailSettingsTestForm
)
from apps.core.ad_services import ActiveDirectoryService
from apps.core.email_services import EmailNotificationService

def is_admin_or_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser or user.groups.filter(name='Super Administrator').exists())

@login_required
@user_passes_test(is_admin_or_staff)
def user_management_list(request):
    """
    UI-Friendly User Management Portal for Admins.
    Lists all users with their Role badges, Departments, and quick action controls.
    """
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    dept_filter = request.GET.get('dept', '').strip()

    users = User.objects.select_related('evaluator_profile__department').prefetch_related('groups').all()

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(evaluator_profile__employee_id__icontains=search_query) |
            Q(evaluator_profile__designation__icontains=search_query)
        )

    if role_filter:
        if role_filter == 'admin':
            users = users.filter(Q(is_superuser=True) | Q(groups__name='Super Administrator'))
        elif role_filter == 'executive':
            users = users.filter(groups__name='Executive Viewer')
        elif role_filter == 'evaluator':
            users = users.filter(groups__name='Evaluator')

    if dept_filter:
        users = users.filter(evaluator_profile__department__id=dept_filter)

    users = users.order_by('-date_joined')

    # Quick summary counts
    total_count = User.objects.count()
    admin_count = User.objects.filter(Q(is_superuser=True) | Q(groups__name='Super Administrator')).distinct().count()
    exec_count = User.objects.filter(groups__name='Executive Viewer').count()
    eval_count = User.objects.filter(groups__name='Evaluator').count()
    departments = Department.objects.all().order_by('name')
    groups = Group.objects.prefetch_related('permissions').all().order_by('name')

    context = {
        'users': users,
        'departments': departments,
        'groups': groups,
        'search_query': search_query,
        'role_filter': role_filter,
        'dept_filter': dept_filter,
        'total_count': total_count,
        'admin_count': admin_count,
        'exec_count': exec_count,
        'eval_count': eval_count,
    }
    return render(request, 'core/user_list.html', context)

@login_required
@user_passes_test(is_admin_or_staff)
def user_create_view(request):
    """
    Friendly UI form to create an Administrator, Executive, or Evaluator.
    """
    if request.method == 'POST':
        form = UserRoleAdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            role_label = dict(form.fields['role'].choices).get(form.cleaned_data.get('role'), 'User')
            messages.success(request, f"Successfully created {role_label}: {user.get_full_name() or user.username} ({user.email})")
            return redirect('user_management_list')
    else:
        initial_role = request.GET.get('role', 'evaluator')
        form = UserRoleAdminCreationForm(initial={'role': initial_role})

    return render(request, 'core/user_form.html', {'form': form, 'title': 'Provision New User Account', 'is_create': True})


@login_required
@user_passes_test(is_admin_or_staff)
def user_provision_from_ad(request):
    """
    Dedicated interface for provisioning users directly from organization Active Directory.
    Selecting an email auto-populates Username, First Name, Last Name, and Official Designation.
    Administrator then selects the AMCE Department, Role (Evaluator, Executive, Admin), and privileges.
    """
    from django.http import JsonResponse

    if request.method == 'POST':
        form = UserFromADProvisionForm(request.POST)
        if form.is_valid():
            user = form.save()
            role_label = dict(form.fields['role'].choices).get(form.cleaned_data.get('role'), 'User')
            messages.success(request, f"Successfully provisioned from AD ({role_label}): {user.get_full_name() or user.username} ({user.email})")
            return redirect('user_management_list')
    else:
        # Pre-select email if passed via GET query
        initial_email = request.GET.get('email', '')
        initial_data = {}
        if initial_email:
            ad_user = ActiveDirectoryService.get_user_by_email(initial_email)
            if ad_user:
                initial_data = {
                    'ad_user_select': ad_user['email'],
                    'email': ad_user['email'],
                    'first_name': ad_user['first_name'],
                    'last_name': ad_user['last_name'],
                    'designation': ad_user['designation'],
                }
        form = UserFromADProvisionForm(initial=initial_data)

    directory_users = ActiveDirectoryService.search_users()

    context = {
        'form': form,
        'directory_users': directory_users,
        'title': 'Provision User from Active Directory',
        'is_azure_ad_live': ActiveDirectoryService.is_azure_ad_configured(),
    }
    return render(request, 'core/user_provision_ad.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def ad_user_lookup_api(request):
    """
    AJAX endpoint to query Active Directory user by email or search term.
    Returns JSON representation of user attributes for immediate form autofill.
    """
    from django.http import JsonResponse
    email = request.GET.get('email', '').strip()
    q = request.GET.get('q', '').strip()

    if email:
        user_info = ActiveDirectoryService.get_user_by_email(email)
        return JsonResponse({'success': bool(user_info), 'user': user_info})

    results = ActiveDirectoryService.search_users(q)
    return JsonResponse({'success': True, 'results': results})


@login_required
@user_passes_test(is_admin_or_staff)
def user_edit_view(request, user_id):
    """
    Edit existing user, change role between Admin, Executive, and Evaluator, and update hospital profile.
    """
    user_obj = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = UserRoleAdminChangeForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"User profile for {user_obj.username} successfully updated.")
            return redirect('user_management_list')
    else:
        form = UserRoleAdminChangeForm(instance=user_obj)

    return render(request, 'core/user_form.html', {'form': form, 'title': f"Edit User: {user_obj.username}", 'is_create': False, 'target_user': user_obj})

@login_required
@user_passes_test(is_admin_or_staff)
def user_toggle_active(request, user_id):
    """
    Deactivates or activates a user account safely.
    """
    if request.method == 'POST':
        user_obj = get_object_or_404(User, pk=user_id)
        if user_obj == request.user:
            messages.error(request, "You cannot deactivate your own active session.")
        else:
            user_obj.is_active = not user_obj.is_active
            user_obj.save()
            status = "activated" if user_obj.is_active else "deactivated"
            messages.info(request, f"User {user_obj.username} has been {status}.")
    return redirect('user_management_list')


@login_required
@user_passes_test(is_admin_or_staff)
def user_set_role(request, user_id):
    """
    Direct Access Control action to grant, change, or remove roles
    (Evaluator, Executive Viewer, Administrator, or Revoke Access).
    """
    if request.method == 'POST':
        user_obj = get_object_or_404(User, pk=user_id)
        new_role = request.POST.get('role', '').strip().lower()

        if user_obj == request.user and new_role in ['evaluator', 'executive', 'none', 'revoke']:
            messages.error(request, "Security protection: You cannot revoke your own administrator privileges.")
            return redirect('user_management_list')

        # Clear existing access groups
        user_obj.groups.clear()

        if new_role == 'admin':
            user_obj.is_staff = True
            user_obj.is_superuser = True
            user_obj.is_active = True
            g, _ = Group.objects.get_or_create(name='Super Administrator')
            user_obj.groups.add(g)
            user_obj.save()
            messages.success(request, f"Granted Super Administrator access to {user_obj.username}.")

        elif new_role == 'executive':
            user_obj.is_staff = False
            user_obj.is_superuser = False
            user_obj.is_active = True
            g, _ = Group.objects.get_or_create(name='Executive Viewer')
            user_obj.groups.add(g)
            user_obj.save()
            messages.success(request, f"Access updated: {user_obj.username} is now an Executive Viewer.")

        elif new_role == 'evaluator':
            user_obj.is_staff = False
            user_obj.is_superuser = False
            user_obj.is_active = True
            g, _ = Group.objects.get_or_create(name='Evaluator')
            user_obj.groups.add(g)
            user_obj.save()
            messages.success(request, f"Access updated: {user_obj.username} is now an Evaluator.")

        elif new_role in ['revoke', 'none']:
            # Revoke all roles and deactivate account
            user_obj.is_staff = False
            user_obj.is_superuser = False
            user_obj.is_active = False
            user_obj.save()
            messages.warning(request, f"Access Revoked: All evaluation and executive roles removed from {user_obj.username}, and account deactivated.")
        else:
            messages.error(request, "Invalid role selection.")

    return redirect('user_management_list')


@login_required
@user_passes_test(is_admin_or_staff)
def user_toggle_permission(request, user_id):
    """
    AJAX / POST endpoint to quickly toggle individual user capability permissions
    ('can_view_executive_dashboard' or 'can_export_scorecard_excel') directly from user list.
    """
    if request.method == 'POST':
        from django.contrib.auth.models import Permission
        user_obj = get_object_or_404(User, pk=user_id)
        perm_code = request.POST.get('permission', '').strip()

        if perm_code not in ['can_view_executive_dashboard', 'can_export_scorecard_excel']:
            messages.error(request, "Invalid permission requested.")
            return redirect('user_management_list')

        perm = Permission.objects.filter(codename=perm_code, content_type__app_label='analytics').first()
        if not perm:
            messages.error(request, "Permission object not found in system.")
            return redirect('user_management_list')

        perm_label = "Executive Dashboard" if perm_code == 'can_view_executive_dashboard' else "Excel Export"

        if user_obj.user_permissions.filter(id=perm.id).exists():
            user_obj.user_permissions.remove(perm)
            messages.info(request, f"Revoked '{perm_label}' access from {user_obj.username}.")
        else:
            user_obj.user_permissions.add(perm)
            messages.success(request, f"Granted '{perm_label}' access to {user_obj.username}.")

    return redirect('user_management_list')


@login_required
@user_passes_test(is_admin_or_staff)
def group_permission_toggle(request, group_id):
    """
    Enables administrators to grant or revoke Executive Dashboard or Excel Export
    across an entire Group (e.g. Evaluator group).
    """
    if request.method == 'POST':
        from django.contrib.auth.models import Permission, Group
        group = get_object_or_404(Group, pk=group_id)
        perm_code = request.POST.get('permission', '').strip()

        if perm_code not in ['can_view_executive_dashboard', 'can_export_scorecard_excel']:
            messages.error(request, "Invalid permission requested.")
            return redirect('user_management_list')

        perm = Permission.objects.filter(codename=perm_code, content_type__app_label='analytics').first()
        if not perm:
            messages.error(request, "Permission definition not found.")
            return redirect('user_management_list')

        perm_label = "Executive Dashboard" if perm_code == 'can_view_executive_dashboard' else "Excel Export"

        if group.permissions.filter(id=perm.id).exists():
            group.permissions.remove(perm)
            messages.info(request, f"Revoked '{perm_label}' from all users in the '{group.name}' group.")
        else:
            group.permissions.add(perm)
            messages.success(request, f"Granted '{perm_label}' to all users in the '{group.name}' group.")

    return redirect('user_management_list')


# ==============================================================================
# ADMIN OPERATIONS HUB & MODULE VIEWS
# ==============================================================================


from apps.vendors.models import Vendor
from apps.schedules.models import MasterCalendar
from apps.forms_builder.models import EvaluationCohort, FormTemplate, CriterionQuestion
from apps.evaluations.models import Submission
from apps.core.forms import VendorForm, MasterCalendarForm, EvaluationCohortForm, CriterionQuestionForm
from django.utils import timezone


@login_required
@user_passes_test(is_admin_or_staff)
def admin_hub(request):
    """
    Central Executive & Operational Admin Hub.
    Consolidates system status, quick KPIs, and direct links to all admin modules.
    """
    users_count = User.objects.count()
    vendors_count = Vendor.objects.count()
    active_vendors = Vendor.objects.filter(is_active=True).count()
    calendar_slots = MasterCalendar.objects.select_related('vendor').all()
    cohorts = EvaluationCohort.objects.all()
    total_weight = sum(c.default_weight for c in cohorts)
    submissions = Submission.objects.select_related('evaluator__user', 'vendor', 'cohort').all()
    
    context = {
        'users_count': users_count,
        'vendors_count': vendors_count,
        'active_vendors': active_vendors,
        'calendar_slots': calendar_slots,
        'calendar_count': calendar_slots.count(),
        'cohorts_count': cohorts.count(),
        'total_weight': total_weight,
        'submissions_count': submissions.count(),
        'draft_submissions': submissions.filter(status='DRAFT').count(),
        'submitted_submissions': submissions.filter(status='SUBMITTED').count(),
        'locked_submissions': submissions.filter(status='LOCKED').count(),
        'recent_submissions': submissions.order_by('-updated_at')[:8],
    }
    return render(request, 'core/admin_portal/hub.html', context)


# --- VENDOR MANAGEMENT ---

@login_required
@user_passes_test(is_admin_or_staff)
def admin_vendor_list(request):
    vendors = Vendor.objects.prefetch_related('calendar_slots').all().order_by('name')
    return render(request, 'core/admin_portal/vendors.html', {'vendors': vendors})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_vendor_create(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            vendor = form.save()
            messages.success(request, f"Vendor '{vendor.name}' added successfully.")
            return redirect('admin_vendor_list')
    else:
        form = VendorForm()
    return render(request, 'core/admin_portal/vendor_form.html', {'form': form, 'title': 'Register New EHR Vendor', 'is_create': True})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_vendor_edit(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, f"Vendor '{vendor.name}' profile updated successfully.")
            return redirect('admin_vendor_list')
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'core/admin_portal/vendor_form.html', {'form': form, 'title': f"Edit Vendor: {vendor.name}", 'vendor': vendor, 'is_create': False})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_vendor_toggle(request, vendor_id):
    if request.method == 'POST':
        vendor = get_object_or_404(Vendor, pk=vendor_id)
        vendor.is_active = not vendor.is_active
        vendor.save()
        messages.info(request, f"Vendor '{vendor.name}' status set to {'Active' if vendor.is_active else 'Inactive'}.")
    return redirect('admin_vendor_list')


# --- CALENDAR & DEMO SLOTS ---

@login_required
@user_passes_test(is_admin_or_staff)
def admin_calendar_list(request):
    schedules = MasterCalendar.objects.select_related('vendor').all().order_by('evaluation_date')
    vendors = Vendor.objects.all().order_by('name')
    return render(request, 'core/admin_portal/schedules.html', {'schedules': schedules, 'vendors': vendors})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_calendar_create(request):
    if request.method == 'POST':
        form = MasterCalendarForm(request.POST)
        if form.is_valid():
            slot = form.save()
            messages.success(request, f"Demonstration slot for {slot.day_label} ({slot.evaluation_date}) created.")
            return redirect('admin_calendar_list')
    else:
        form = MasterCalendarForm()
    return render(request, 'core/admin_portal/calendar_form.html', {'form': form, 'title': 'Schedule Demonstration Day Slot', 'is_create': True})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_calendar_edit(request, slot_id):
    slot = get_object_or_404(MasterCalendar, pk=slot_id)
    if request.method == 'POST':
        form = MasterCalendarForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, f"Calendar slot for {slot.day_label} updated.")
            return redirect('admin_calendar_list')
    else:
        form = MasterCalendarForm(instance=slot)
    return render(request, 'core/admin_portal/calendar_form.html', {'form': form, 'title': f"Edit Slot: {slot.day_label}", 'slot': slot, 'is_create': False})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_calendar_set_status(request, slot_id):
    if request.method == 'POST':
        slot = get_object_or_404(MasterCalendar, pk=slot_id)
        new_status = request.POST.get('status')
        valid_statuses = [choice[0] for choice in MasterCalendar.STATUS_CHOICES]
        if new_status in valid_statuses:
            slot.status = new_status
            slot.save()
            messages.success(request, f"Calendar status for {slot.day_label} updated to '{slot.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status choice selected.")
    return redirect('admin_calendar_list')


# --- COHORTS & CRITERIA ---

@login_required
@user_passes_test(is_admin_or_staff)
def admin_cohorts_list(request):
    cohorts = EvaluationCohort.objects.prefetch_related('templates__criteria').all().order_by('cohort_number')
    total_weight = sum(c.default_weight for c in cohorts)
    return render(request, 'core/admin_portal/cohorts.html', {'cohorts': cohorts, 'total_weight': total_weight})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_cohort_edit(request, cohort_id):
    cohort = get_object_or_404(EvaluationCohort, pk=cohort_id)
    if request.method == 'POST':
        form = EvaluationCohortForm(request.POST, instance=cohort)
        if form.is_valid():
            form.save()
            messages.success(request, f"Cohort #{cohort.cohort_number} ({cohort.name}) updated.")
            return redirect('admin_cohorts_list')
    else:
        form = EvaluationCohortForm(instance=cohort)
    return render(request, 'core/admin_portal/cohort_form.html', {'form': form, 'cohort': cohort, 'title': f"Edit Cohort #{cohort.cohort_number}: {cohort.name}"})


@login_required
@user_passes_test(is_admin_or_staff)
def admin_cohort_criteria(request, cohort_id):
    cohort = get_object_or_404(EvaluationCohort, pk=cohort_id)
    template = cohort.templates.first()
    if not template:
        template = FormTemplate.objects.create(
            cohort=cohort,
            version='1.0.0',
            title=f"{cohort.name} Scoring Template",
            created_by=request.user
        )
    criteria = template.criteria.all().order_by('criterion_number')
    total_criterion_weight = sum(c.weight_percentage for c in criteria)
    return render(request, 'core/admin_portal/criteria_list.html', {
        'cohort': cohort,
        'template': template,
        'criteria': criteria,
        'total_criterion_weight': total_criterion_weight
    })


@login_required
@user_passes_test(is_admin_or_staff)
def admin_criterion_create(request, cohort_id):
    cohort = get_object_or_404(EvaluationCohort, pk=cohort_id)
    template = cohort.templates.first()
    if request.method == 'POST':
        form = CriterionQuestionForm(request.POST)
        if form.is_valid():
            crit = form.save(commit=False)
            crit.template = template
            crit.save()
            messages.success(request, f"Criterion #{crit.criterion_number} added.")
            return redirect('admin_cohort_criteria', cohort_id=cohort.id)
    else:
        next_num = (template.criteria.count() + 1) if template else 1
        form = CriterionQuestionForm(initial={'criterion_number': next_num})
    return render(request, 'core/admin_portal/criterion_form.html', {
        'form': form,
        'cohort': cohort,
        'title': f"Add Criterion to Cohort #{cohort.cohort_number}",
        'is_create': True
    })


@login_required
@user_passes_test(is_admin_or_staff)
def admin_criterion_edit(request, cohort_id, criterion_id):
    cohort = get_object_or_404(EvaluationCohort, pk=cohort_id)
    crit = get_object_or_404(CriterionQuestion, pk=criterion_id)
    if request.method == 'POST':
        form = CriterionQuestionForm(request.POST, instance=crit)
        if form.is_valid():
            form.save()
            messages.success(request, f"Criterion #{crit.criterion_number} updated.")
            return redirect('admin_cohort_criteria', cohort_id=cohort.id)
    else:
        form = CriterionQuestionForm(instance=crit)
    return render(request, 'core/admin_portal/criterion_form.html', {
        'form': form,
        'cohort': cohort,
        'crit': crit,
        'title': f"Edit Criterion #{crit.criterion_number}",
        'is_create': False
    })


# --- SUBMISSIONS & MODERATION OVERSIGHT ---

@login_required
@user_passes_test(is_admin_or_staff)
def admin_submissions_list(request):
    status_filter = request.GET.get('status', '').strip()
    vendor_filter = request.GET.get('vendor', '').strip()
    cohort_filter = request.GET.get('cohort', '').strip()

    submissions = Submission.objects.select_related(
        'evaluator__user', 'evaluator__department', 'vendor', 'cohort', 'calendar'
    ).all().order_by('-updated_at')

    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if vendor_filter:
        submissions = submissions.filter(vendor__id=vendor_filter)
    if cohort_filter:
        submissions = submissions.filter(cohort__id=cohort_filter)

    vendors = Vendor.objects.all().order_by('name')
    cohorts = EvaluationCohort.objects.all().order_by('cohort_number')

    context = {
        'submissions': submissions,
        'vendors': vendors,
        'cohorts': cohorts,
        'status_filter': status_filter,
        'vendor_filter': vendor_filter,
        'cohort_filter': cohort_filter,
        'total_submissions': Submission.objects.count(),
        'locked_count': Submission.objects.filter(status='LOCKED').count(),
        'submitted_count': Submission.objects.filter(status='SUBMITTED').count(),
        'draft_count': Submission.objects.filter(status='DRAFT').count(),
    }
    return render(request, 'core/admin_portal/submissions.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def admin_submission_toggle_lock(request, submission_id):
    if request.method == 'POST':
        sub = get_object_or_404(Submission, submission_id=submission_id)
        if sub.status == 'LOCKED':
            sub.status = 'SUBMITTED'
            sub.locked_at = None
            sub.save()
            messages.warning(request, f"Submission {sub.submission_id} has been UNLOCKED for revision.")
        else:
            sub.status = 'LOCKED'
            sub.locked_at = timezone.now()
            sub.record_hash = sub.generate_integrity_hash()
            sub.save()
            messages.success(request, f"Submission {sub.submission_id} is now LOCKED and sealed with cryptographic integrity hash.")
    return redirect('admin_submissions_list')


@login_required
@user_passes_test(is_admin_or_staff)
def admin_submission_printout(request, submission_id):
    """
    Renders an official, executive-ready, print-optimized evaluation scorecard
    for an individual submission. Formatted for high-quality printing / PDF export.
    """
    sub = get_object_or_404(
        Submission.objects.select_related(
            'evaluator__user', 'evaluator__department',
            'vendor', 'cohort', 'calendar', 'template'
        ),
        submission_id=submission_id
    )

    # Prefetch responses with criteria ordered by criterion_number
    responses = sub.responses.select_related('criterion').order_by('criterion__criterion_number')
    
    # Calculate summary metrics
    total_criteria = responses.count()
    scored_criteria = sum(1 for r in responses if r.score is not None and r.score > 0)
    raw_score_sum = sum((r.score or Decimal('0.0')) for r in responses)
    avg_score = (raw_score_sum / Decimal(str(scored_criteria))) if scored_criteria > 0 else Decimal('0.0')

    context = {
        'sub': sub,
        'responses': responses,
        'total_criteria': total_criteria,
        'scored_criteria': scored_criteria,
        'avg_score': avg_score,
        'print_time': timezone.now(),
    }
    return render(request, 'core/admin_portal/submission_printout.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def admin_submissions_print_all(request):
    """
    Renders all filtered submissions sequentially in a clean, print-optimized format
    with automatic page breaks between scorecards, ideal for 'Print All' or 'Save all as PDF'.
    """
    status_filter = request.GET.get('status', '').strip()
    vendor_filter = request.GET.get('vendor', '').strip()
    cohort_filter = request.GET.get('cohort', '').strip()

    submissions = Submission.objects.select_related(
        'evaluator__user', 'evaluator__department',
        'vendor', 'cohort', 'calendar', 'template'
    ).all().order_by('cohort__cohort_number', 'vendor__name', 'evaluator__user__last_name')

    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if vendor_filter:
        submissions = submissions.filter(vendor__id=vendor_filter)
    if cohort_filter:
        submissions = submissions.filter(cohort__id=cohort_filter)

    submissions_data = []
    for sub in submissions:
        responses = sub.responses.select_related('criterion').order_by('criterion__criterion_number')
        total_criteria = responses.count()
        scored_criteria = sum(1 for r in responses if r.score is not None and r.score > 0)
        raw_score_sum = sum((r.score or Decimal('0.0')) for r in responses)
        avg_score = (raw_score_sum / Decimal(str(scored_criteria))) if scored_criteria > 0 else Decimal('0.0')

        submissions_data.append({
            'sub': sub,
            'responses': responses,
            'total_criteria': total_criteria,
            'scored_criteria': scored_criteria,
            'avg_score': avg_score,
        })

    context = {
        'submissions_data': submissions_data,
        'print_time': timezone.now(),
        'query_string': request.GET.urlencode(),
    }
    return render(request, 'core/admin_portal/submissions_print_all.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def admin_submissions_export_all_excel(request):
    """
    Generates a multi-tab Microsoft Excel workbook (.xlsx):
    - Tab 1: 'All Submissions Audit' (Comprehensive list with SHA-256 hashes, statuses, evaluator names, vendors, cohorts, and scores)
    - Tab 2: 'Detailed Criteria Responses' (Itemized criteria breakdown with prompt, evaluator score, weighted score, and observation notes)
    """
    import io
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from django.http import HttpResponse

    status_filter = request.GET.get('status', '').strip()
    vendor_filter = request.GET.get('vendor', '').strip()
    cohort_filter = request.GET.get('cohort', '').strip()

    submissions = Submission.objects.select_related(
        'evaluator__user', 'evaluator__department',
        'vendor', 'cohort', 'calendar', 'template'
    ).all().order_by('cohort__cohort_number', 'vendor__name', 'evaluator__user__last_name')

    if status_filter:
        submissions = submissions.filter(status=status_filter)
    if vendor_filter:
        submissions = submissions.filter(vendor__id=vendor_filter)
    if cohort_filter:
        submissions = submissions.filter(cohort__id=cohort_filter)

    wb = openpyxl.Workbook()

    # Styling
    navy_fill = PatternFill(start_color="0B2545", end_color="0B2545", fill_type="solid")
    teal_fill = PatternFill(start_color="139A8C", end_color="139A8C", fill_type="solid")
    white_bold = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=13, bold=True, color="0B2545")
    bold_font = Font(name="Calibri", size=11, bold=True)
    regular_font = Font(name="Calibri", size=11)

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # --- Sheet 1: Master Submissions Registry ---
    ws1 = wb.active
    ws1.title = "Submissions Registry"

    ws1.merge_cells("A1:J1")
    ws1["A1"] = "AMCE EHR Demonstration Evaluation - Submissions Audit Registry"
    ws1["A1"].font = title_font
    ws1["A1"].alignment = Alignment(horizontal="left", vertical="center")

    headers1 = [
        "Submission ID", "Status", "Clinical Evaluator", "Evaluator Email",
        "Department", "Designation", "Assigned Vendor", "Cohort", "Weighted Score (%)", "Cryptographic Hash (SHA-256)"
    ]
    ws1.append([])
    ws1.append(headers1)
    header_row_idx = 3

    for col_idx, col_name in enumerate(headers1, start=1):
        cell = ws1.cell(row=header_row_idx, column=col_idx)
        cell.font = white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 2, 9] else "left", vertical="center")
        cell.border = thin_border

    current_row = 4
    for sub in submissions:
        row_vals = [
            sub.submission_id,
            sub.get_status_display(),
            sub.evaluator.user.get_full_name() or sub.evaluator.user.username,
            sub.evaluator.user.email,
            sub.evaluator.department.name if sub.evaluator and sub.evaluator.department else "—",
            sub.evaluator.designation if sub.evaluator else "—",
            sub.vendor.name if sub.vendor else "—",
            f"#{sub.cohort.cohort_number} - {sub.cohort.name}" if sub.cohort else "—",
            float(sub.total_group_score),
            sub.record_hash or "Pending Seal"
        ]
        ws1.append(row_vals)
        for c_idx in range(1, len(row_vals) + 1):
            cell = ws1.cell(row=current_row, column=c_idx)
            cell.font = regular_font
            cell.border = thin_border
            if c_idx in [1, 2, 9]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
        current_row += 1

    # --- Sheet 2: Detailed Criteria Responses Breakdown ---
    ws2 = wb.create_sheet(title="Detailed Criteria Breakdown")

    ws2.merge_cells("A1:K1")
    ws2["A1"] = "AMCE EHR Demonstration - Granular Criteria Scores & Evaluator Observations"
    ws2["A1"].font = title_font
    ws2["A1"].alignment = Alignment(horizontal="left", vertical="center")

    headers2 = [
        "Submission ID", "Vendor", "Cohort", "Evaluator Name",
        "Criterion #", "Criterion Name", "Demo Prompt", "Weight (%)", "Raw Score (1-5)", "Weighted Score (%)", "Observations & Notes"
    ]
    ws2.append([])
    ws2.append(headers2)
    header_row_idx2 = 3

    for col_idx, col_name in enumerate(headers2, start=1):
        cell = ws2.cell(row=header_row_idx2, column=col_idx)
        cell.font = white_bold
        cell.fill = teal_fill
        cell.alignment = Alignment(horizontal="center" if col_idx in [1, 5, 8, 9, 10] else "left", vertical="center")
        cell.border = thin_border

    current_row2 = 4
    for sub in submissions:
        responses = sub.responses.select_related('criterion').order_by('criterion__criterion_number')
        for resp in responses:
            row_vals2 = [
                sub.submission_id,
                sub.vendor.name if sub.vendor else "—",
                sub.cohort.name if sub.cohort else "—",
                sub.evaluator.user.get_full_name() or sub.evaluator.user.username,
                resp.criterion.criterion_number,
                resp.criterion.name,
                resp.criterion.demo_prompt,
                float(resp.criterion.weight_percentage),
                float(resp.score) if resp.score is not None else 0.0,
                float(resp.weighted_score),
                resp.evidence_notes or ""
            ]
            ws2.append(row_vals2)
            for c_idx in range(1, len(row_vals2) + 1):
                cell = ws2.cell(row=current_row2, column=c_idx)
                cell.font = regular_font
                cell.border = thin_border
                if c_idx in [1, 5, 8, 9, 10]:
                    cell.alignment = Alignment(horizontal="center", vertical="center")
            current_row2 += 1

    # Adjust column widths
    ws1.column_dimensions['A'].width = 22
    ws1.column_dimensions['B'].width = 14
    ws1.column_dimensions['C'].width = 24
    ws1.column_dimensions['D'].width = 26
    ws1.column_dimensions['E'].width = 22
    ws1.column_dimensions['F'].width = 22
    ws1.column_dimensions['G'].width = 18
    ws1.column_dimensions['H'].width = 28
    ws1.column_dimensions['I'].width = 18
    ws1.column_dimensions['J'].width = 45

    ws2.column_dimensions['A'].width = 22
    ws2.column_dimensions['B'].width = 16
    ws2.column_dimensions['C'].width = 24
    ws2.column_dimensions['D'].width = 22
    ws2.column_dimensions['E'].width = 12
    ws2.column_dimensions['F'].width = 30
    ws2.column_dimensions['G'].width = 40
    ws2.column_dimensions['H'].width = 12
    ws2.column_dimensions['I'].width = 14
    ws2.column_dimensions['J'].width = 18
    ws2.column_dimensions['K'].width = 45

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="AMCE_All_Scorecards_Comprehensive_Export.xlsx"'
    return response


# ==============================================================================
# DYNAMIC MESSAGE TEMPLATES, EMAIL SETUP & NOTIFICATION LOGS
# ==============================================================================

@login_required
@user_passes_test(is_admin_or_staff)
def admin_email_templates_list(request):
    """
    Overview list of all dynamic message templates in the system.
    Initializes default templates if they don't exist yet.
    """
    # Ensure default templates are present in DB
    for event_key in EmailNotificationService.DEFAULT_TEMPLATES.keys():
        EmailNotificationService.get_or_create_template(event_key)

    templates = EmailMessageTemplate.objects.all().order_by('event_type')
    recent_logs = EmailNotificationLog.objects.all()[:10]

    context = {
        'templates': templates,
        'recent_logs': recent_logs,
        'total_logs_count': EmailNotificationLog.objects.count(),
        'sent_count': EmailNotificationLog.objects.filter(status='SENT').count(),
        'failed_count': EmailNotificationLog.objects.filter(status='FAILED').count(),
    }
    return render(request, 'core/email_templates/list.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def admin_email_template_edit(request, template_id):
    """
    Edit dynamic email template subject, sender headers, HTML body, and variables.
    """
    tpl = get_object_or_404(EmailMessageTemplate, pk=template_id)
    if request.method == 'POST':
        form = EmailMessageTemplateForm(request.POST, instance=tpl)
        if form.is_valid():
            form.save()
            messages.success(request, f"Message template '{tpl.title}' updated successfully.")
            return redirect('admin_email_templates_list')
    else:
        form = EmailMessageTemplateForm(instance=tpl)

    return render(request, 'core/email_templates/form.html', {
        'form': form,
        'tpl': tpl,
        'title': f"Edit Message Template: {tpl.title}",
    })


@login_required
@user_passes_test(is_admin_or_staff)
def admin_email_template_preview(request, template_id):
    """
    Renders a live HTML preview of the template with sample dynamic variable substitutions.
    """
    from django.conf import settings
    tpl = get_object_or_404(EmailMessageTemplate, pk=template_id)

    domain = getattr(settings, 'SITE_DOMAIN', 'http://127.0.0.1:8089').rstrip('/')
    sample_context = {
        'first_name': 'Amina',
        'last_name': 'Bello',
        'email': 'a.bello@amce.org',
        'username': 'a.bello@amce.org',
        'role': 'Clinical Evaluator',
        'department': 'Nursing Services',
        'designation': 'Nurse Manager - ICU & Inpatient',
        'login_url': f"{domain}/login/",
        'password_note': "<strong>Initial Security Password:</strong> <code style='background: #e2e8f0; padding: 2px 6px; border-radius: 4px;'>AmceEval2026!</code>",
        'portal_name': 'AMCE Vendor Evaluation Portal',
    }

    rendered_html = tpl.body_html
    rendered_subject = tpl.subject
    for k, v in sample_context.items():
        rendered_html = rendered_html.replace(f"{{{{{k}}}}}", str(v))
        rendered_subject = rendered_subject.replace(f"{{{{{k}}}}}", str(v))

    return render(request, 'core/email_templates/preview.html', {
        'tpl': tpl,
        'rendered_html': rendered_html,
        'rendered_subject': rendered_subject,
        'sample_context': sample_context,
    })


@login_required
@user_passes_test(is_admin_or_staff)
def admin_email_settings_view(request):
    """
    Operational Email Message Setup:
    - View active SMTP / Exchange / Office 365 / Console email configuration.
    - Test sending a live verification email to any specified address.
    """
    from django.conf import settings
    from django.core.mail import send_mail

    test_form = EmailSettingsTestForm()

    current_backend = getattr(settings, 'EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
    is_smtp = 'smtp' in current_backend.lower()
    has_smtp_creds = bool(getattr(settings, 'EMAIL_HOST_USER', '')) and bool(getattr(settings, 'EMAIL_HOST_PASSWORD', ''))

    if is_smtp:
        subsystem_status = "Operational" if has_smtp_creds else "Non-operational"
    else:
        subsystem_status = "Simulated (Dev)"

    if request.method == 'POST' and 'send_test_email' in request.POST:
        test_form = EmailSettingsTestForm(request.POST)
        if test_form.is_valid():
            recipient = test_form.cleaned_data['test_recipient']
            if is_smtp and not has_smtp_creds:
                messages.error(request, "Mail delivery Subsystem is Non-operational: SMTP backend selected but EMAIL_HOST_USER / EMAIL_HOST_PASSWORD credentials are not configured in your environment or .env file.")
            else:
                try:
                    send_mail(
                        subject="[Test] AMCE Vendor Evaluation System - Email Verification",
                        message="This is a test notification verifying that the AMCE Vendor Evaluation email delivery subsystem is operating properly.",
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient],
                        fail_silently=False
                    )
                    status_log = 'SENT' if is_smtp else 'SIMULATED'
                    EmailNotificationLog.objects.create(
                        recipient_user=request.user,
                        recipient_email=recipient,
                        subject="[Test] AMCE Vendor Evaluation System - Email Verification",
                        body_snapshot="Live SMTP / Backend Connectivity Verification Email",
                        event_type="TEST_EMAIL",
                        status=status_log
                    )
                    if is_smtp:
                        messages.success(request, f"Verification email successfully dispatched via SMTP to '{recipient}'. Please check your inbox.")
                    else:
                        messages.warning(request, f"Mail delivery Subsystem is currently in Development/Console mode (ConsoleBackend). Email was logged to console/audit trail only and not transmitted over the internet to '{recipient}'. Set EMAIL_BACKEND to SMTP with valid credentials to deliver live internet emails.")
                except Exception as e:
                    EmailNotificationLog.objects.create(
                        recipient_user=request.user,
                        recipient_email=recipient,
                        subject="[Test] AMCE Vendor Evaluation System - Email Verification",
                        body_snapshot="Live SMTP / Backend Connectivity Verification Email",
                        event_type="TEST_EMAIL",
                        status="FAILED",
                        error_message=str(e)
                    )
                    messages.error(request, f"Failed to send email to '{recipient}': {e}")
            return redirect('admin_email_settings')

    context = {
        'test_form': test_form,
        'email_backend': current_backend,
        'email_host': getattr(settings, 'EMAIL_HOST', 'smtp.office365.com'),
        'email_port': getattr(settings, 'EMAIL_PORT', 587),
        'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', True),
        'email_host_user': getattr(settings, 'EMAIL_HOST_USER', '') or '(Not configured - credentials missing)',
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@amce.org'),
        'site_domain': getattr(settings, 'SITE_DOMAIN', 'http://127.0.0.1:8089'),
        'subsystem_status': subsystem_status,
        'is_smtp': is_smtp,
        'has_smtp_creds': has_smtp_creds,
        'recent_logs': EmailNotificationLog.objects.all()[:8],
    }
    return render(request, 'core/email_templates/settings.html', context)


@login_required
@user_passes_test(is_admin_or_staff)
def admin_email_logs_list(request):
    """
    Searchable audit trail of all emails sent by the system.
    """
    logs = EmailNotificationLog.objects.all().order_by('-sent_at')
    return render(request, 'core/email_templates/logs.html', {'logs': logs})



