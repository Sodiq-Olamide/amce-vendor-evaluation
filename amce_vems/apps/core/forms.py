from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from apps.core.models import Department, EvaluatorProfile

ROLE_CHOICES = [
    ('evaluator', 'Evaluator (Scores demonstration cohorts)'),
    ('executive', 'Executive Viewer (Executive dashboard & sensitivity simulator)'),
    ('admin', 'System Administrator (Full access & Django admin)'),
]

class UserRoleAdminCreationForm(UserCreationForm):
    """
    User-friendly admin form that lets administrators select a Role
    and creates the corresponding User, Group linkages, and EvaluatorProfile.
    Username automatically synchronizes with the Official AMCE Email address.
    """
    email = forms.EmailField(
        required=True, 
        help_text="Official AMCE email address (serves as the system login username)."
    )
    first_name = forms.CharField(max_length=150, required=True, help_text="First name of the staff member.")
    last_name = forms.CharField(max_length=150, required=True, help_text="Last name / Surname.")
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='evaluator',
        widget=forms.RadioSelect,
        help_text="Select the access level. Permissions, group assignments, and profile setup are handled automatically."
    )
    
    designation = forms.CharField(
        max_length=255, 
        required=False,
        initial="Evaluator / Clinical Specialist",
        help_text="Official hospital title (e.g. Head of Nursing, Chief Medical Officer, IT Systems Analyst)."
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=False,
        help_text="Primary department assigned to this user."
    )

    grant_executive_dashboard = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Grant Executive Dashboard Access",
        help_text="Allow this user to access the Executive Dashboard and Sensitivity Simulator (overrides default Evaluator restriction)."
    )
    grant_export_excel = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Grant Scorecard Excel Export Access",
        help_text="Allow this user to download the high-fidelity multi-vendor Excel scorecard export."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'designation', 'department', 'grant_executive_dashboard', 'grant_export_excel')

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email:
            cleaned_data['username'] = email.strip().lower()
            # Check if a user with this username/email already exists
            if User.objects.filter(username__iexact=cleaned_data['username']).exists():
                self.add_error('email', "A user account with this email/username already exists.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data['email'].strip().lower()
        user.email = email
        user.username = email
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        role = self.cleaned_data.get('role', 'evaluator')
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'executive':
            user.is_staff = False
            user.is_superuser = False
        else: # evaluator
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
            self._apply_role_and_profile(user, role)
        return user

    def _apply_role_and_profile(self, user, role):
        # 1. Assign Group
        user.groups.clear()
        if role == 'admin':
            group_name = 'Super Administrator'
        elif role == 'executive':
            group_name = 'Executive Viewer'
        else:
            group_name = 'Evaluator'
            
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

        # 2. Ensure Department
        dept = self.cleaned_data.get('department')
        if not dept:
            dept = Department.objects.first()

        # 3. Create or Update EvaluatorProfile
        prefix = 'ADM' if role == 'admin' else ('EXE' if role == 'executive' else 'EVL')
        emp_id = f"AMCE-{prefix}-{user.id:04d}"

        designation = self.cleaned_data.get('designation')
        if not designation:
            designation = 'System Administrator' if role == 'admin' else ('Executive Viewer' if role == 'executive' else 'Clinical Evaluator')

        EvaluatorProfile.objects.update_or_create(
            user=user,
            defaults={
                'employee_id': emp_id,
                'designation': designation,
                'department': dept,
                'is_active': True
            }
        )

        # 4. Assign or remove specific custom permissions
        from django.contrib.auth.models import Permission
        p_exec = Permission.objects.filter(codename='can_view_executive_dashboard').first()
        p_export = Permission.objects.filter(codename='can_export_scorecard_excel').first()

        if role == 'evaluator':
            if p_exec:
                if self.cleaned_data.get('grant_executive_dashboard'):
                    user.user_permissions.add(p_exec)
                else:
                    user.user_permissions.remove(p_exec)
            if p_export:
                if self.cleaned_data.get('grant_export_excel'):
                    user.user_permissions.add(p_export)
                else:
                    user.user_permissions.remove(p_export)

        # 5. Automatically send welcome email with credentials
        try:
            from apps.core.email_services import EmailNotificationService
            raw_pw = self.cleaned_data.get('password1')
            EmailNotificationService.send_user_welcome_email(user, password=raw_pw, is_ad_provisioned=False)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error triggering welcome email: {e}")


class UserFromADProvisionForm(forms.Form):
    """
    Dedicated form for provisioning users from Active Directory (Azure AD / LDAP).
    Auto-fills Username, First Name, Last Name, and Official Designation from AD,
    while allowing the Administrator to assign the Department, Role, and Special Privileges.
    """
    ad_user_select = forms.ChoiceField(
        choices=[],
        required=False,
        label="Select Staff Member from Active Directory",
        help_text="Choose an organization staff member to automatically synchronize their profile details."
    )
    email = forms.EmailField(
        required=True,
        label="Official AMCE Email / Login Username",
        help_text="Official email verified from Active Directory."
    )
    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name / Surname")
    designation = forms.CharField(max_length=255, required=False, label="Official Designation (from AD)")
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=True,
        label="Assigned Hospital Department",
        help_text="Select the AMCE clinical or administrative unit for this evaluator."
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial='evaluator',
        widget=forms.RadioSelect,
        label="Account Role & System Access Level"
    )

    grant_executive_dashboard = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Grant Executive Dashboard Access",
        help_text="Allow access to Executive Scorecard and Simulator."
    )
    grant_export_excel = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Grant Scorecard Excel Export Access",
        help_text="Allow downloading multi-vendor Excel reports."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.core.ad_services import ActiveDirectoryService
        directory_users = ActiveDirectoryService.search_users()
        choices = [("", "-- Select a staff member from Active Directory --")]
        for u in directory_users:
            choices.append((u['email'], f"{u['first_name']} {u['last_name']} ({u['email']}) - {u['designation']}"))
        self.fields['ad_user_select'].choices = choices

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise forms.ValidationError(f"An account for '{email}' is already provisioned in the portal.")
        return email

    def save(self):
        from django.utils.crypto import get_random_string
        from django.contrib.auth.models import Permission

        email = self.cleaned_data['email'].strip().lower()
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        designation = self.cleaned_data.get('designation') or "Evaluator / Specialist"
        dept = self.cleaned_data['department']
        role = self.cleaned_data['role']

        # Create user with an unguessable randomized password (they authenticate via AD SSO / LDAP)
        random_pw = get_random_string(32)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=random_pw,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )

        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            g_name = 'Super Administrator'
        elif role == 'executive':
            user.is_staff = False
            user.is_superuser = False
            g_name = 'Executive Viewer'
        else:
            user.is_staff = False
            user.is_superuser = False
            g_name = 'Evaluator'

        user.save()
        group, _ = Group.objects.get_or_create(name=g_name)
        user.groups.add(group)

        # Profile
        emp_id = f"AMCE-AD-{user.id:04d}"
        EvaluatorProfile.objects.create(
            user=user,
            employee_id=emp_id,
            designation=designation,
            department=dept,
            is_active=True
        )

        # Special permissions
        p_exec = Permission.objects.filter(codename='can_view_executive_dashboard').first()
        p_export = Permission.objects.filter(codename='can_export_scorecard_excel').first()
        if role == 'evaluator':
            if p_exec and self.cleaned_data.get('grant_executive_dashboard'):
                user.user_permissions.add(p_exec)
            if p_export and self.cleaned_data.get('grant_export_excel'):
                user.user_permissions.add(p_export)

        # Trigger automatic welcome notification email
        try:
            from apps.core.email_services import EmailNotificationService
            EmailNotificationService.send_user_welcome_email(user, is_ad_provisioned=True)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error triggering AD welcome email: {e}")

        return user


class UserRoleAdminChangeForm(forms.ModelForm):
    """
    Form for modifying existing user details, password, role, and profile details.
    Synchronizes username with email on save.
    """
    email = forms.EmailField(
        required=True, 
        help_text="Official AMCE email address (serves as the system login username)."
    )
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)

    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Leave empty to keep existing password'}),
        required=False,
        help_text="Enter a new password only if you wish to reset or change it."
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm new password'}),
        required=False,
        help_text="Re-type the new password to confirm."
    )

    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        required=False,
        help_text="Update the account role. Group linkages and permissions will synchronize automatically."
    )
    
    designation = forms.CharField(max_length=255, required=False)
    department = forms.ModelChoiceField(queryset=Department.objects.all().order_by('name'), required=False)

    grant_executive_dashboard = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Grant Executive Dashboard Access",
        help_text="Allow this user to access the Executive Dashboard and Sensitivity Simulator (overrides default Evaluator restriction)."
    )
    grant_export_excel = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Grant Scorecard Excel Export Access",
        help_text="Allow this user to download the high-fidelity multi-vendor Excel scorecard export."
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'designation', 'department', 'grant_executive_dashboard', 'grant_export_excel')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Determine current role
            if self.instance.is_superuser or self.instance.groups.filter(name='Super Administrator').exists():
                self.fields['role'].initial = 'admin'
            elif self.instance.groups.filter(name='Executive Viewer').exists():
                self.fields['role'].initial = 'executive'
            else:
                self.fields['role'].initial = 'evaluator'

            # Populate profile fields
            profile = getattr(self.instance, 'evaluator_profile', None)
            if profile:
                self.fields['designation'].initial = profile.designation
                self.fields['department'].initial = profile.department

            # Populate custom permission toggles
            from django.contrib.auth.models import Permission
            has_exec = self.instance.user_permissions.filter(codename='can_view_executive_dashboard').exists() or self.instance.has_perm('analytics.can_view_executive_dashboard')
            has_export = self.instance.user_permissions.filter(codename='can_export_scorecard_excel').exists() or self.instance.has_perm('analytics.can_export_scorecard_excel')
            self.fields['grant_executive_dashboard'].initial = has_exec
            self.fields['grant_export_excel'].initial = has_export

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        if email:
            email_clean = email.strip().lower()
            cleaned_data['username'] = email_clean
            # Check collision with other users
            if User.objects.filter(username__iexact=email_clean).exclude(pk=self.instance.pk).exists():
                self.add_error('email', "Another account already uses this email/username.")

        p1 = cleaned_data.get('new_password')
        p2 = cleaned_data.get('confirm_password')
        if p1 or p2:
            if p1 != p2:
                self.add_error('confirm_password', "The two password fields didn't match.")
            elif len(p1) < 8:
                self.add_error('new_password', "Password must contain at least 8 characters.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            user.email = email
            user.username = email
        
        # Apply new password if provided
        new_pw = self.cleaned_data.get('new_password')
        if new_pw:
            user.set_password(new_pw)

        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'executive':
            user.is_staff = False
            user.is_superuser = False
        elif role == 'evaluator':
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()
            if role:
                user.groups.clear()
                g_name = 'Super Administrator' if role == 'admin' else ('Executive Viewer' if role == 'executive' else 'Evaluator')
                group, _ = Group.objects.get_or_create(name=g_name)
                user.groups.add(group)

            dept = self.cleaned_data.get('department') or Department.objects.first()
            desig = self.cleaned_data.get('designation') or ("Administrator" if role == 'admin' else "Evaluator")

            # Preserve or auto-generate profile employee_id
            existing_profile = getattr(user, 'evaluator_profile', None)
            emp_id = (existing_profile.employee_id if existing_profile and existing_profile.employee_id else f"AMCE-USR-{user.id:04d}")

            EvaluatorProfile.objects.update_or_create(
                user=user,
                defaults={
                    'employee_id': emp_id,
                    'designation': desig,
                    'department': dept,
                    'is_active': user.is_active
                }
            )

            # Sync custom permissions on user object directly
            from django.contrib.auth.models import Permission
            p_exec = Permission.objects.filter(codename='can_view_executive_dashboard').first()
            p_export = Permission.objects.filter(codename='can_export_scorecard_excel').first()

            if p_exec:
                if self.cleaned_data.get('grant_executive_dashboard'):
                    user.user_permissions.add(p_exec)
                else:
                    user.user_permissions.remove(p_exec)

            if p_export:
                if self.cleaned_data.get('grant_export_excel'):
                    user.user_permissions.add(p_export)
                else:
                    user.user_permissions.remove(p_export)
        return user




from apps.vendors.models import Vendor
from apps.schedules.models import MasterCalendar
from apps.forms_builder.models import EvaluationCohort, CriterionQuestion


class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['code', 'name', 'lead_presenter', 'solution_name', 'solution_version', 'contact_email', 'contact_phone', 'overview_description', 'is_active']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. EPIC, CERNER, EZCARE'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Vendor Company Name'}),
            'lead_presenter': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lead Presenter Name'}),
            'solution_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'EHR Solution Product Name'}),
            'solution_version': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2024.1, v12.0'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'vendor@domain.com'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+234 ...'}),
            'overview_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Solution architecture and company overview notes'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class MasterCalendarForm(forms.ModelForm):
    class Meta:
        model = MasterCalendar
        fields = ['evaluation_date', 'day_label', 'vendor', 'status', 'notes']
        widgets = {
            'evaluation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'day_label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Day 1, Day 2'}),
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Demonstration timetable or venue notes'}),
        }


class EvaluationCohortForm(forms.ModelForm):
    class Meta:
        model = EvaluationCohort
        fields = ['cohort_number', 'name', 'slug', 'default_weight', 'target_audience', 'session_time_slot', 'is_active']
        widgets = {
            'cohort_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Nursing Services'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. nursing-services'}),
            'default_weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 15.00'}),
            'target_audience': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Clinical Staff, Nurses, Pharmacists...'}),
            'session_time_slot': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 09:00 - 11:00'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CriterionQuestionForm(forms.ModelForm):
    class Meta:
        model = CriterionQuestion
        fields = ['criterion_number', 'name', 'weight_percentage', 'demo_prompt', 'guidance_notes', 'requires_evidence_threshold']
        widgets = {
            'criterion_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Criterion capability name'}),
            'weight_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'e.g. 15.00'}),
            'demo_prompt': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Live vendor demonstration requirement prompt'}),
            'guidance_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Scoring rubric and instructions'}),
            'requires_evidence_threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


from apps.core.models import EmailMessageTemplate

class EmailMessageTemplateForm(forms.ModelForm):
    class Meta:
        model = EmailMessageTemplate
        fields = ['title', 'subject', 'from_name', 'from_email', 'is_active', 'body_html', 'body_text']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Template Title'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email Subject with tags like {{first_name}}'}),
            'from_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'AMCE Evaluation Committee'}),
            'from_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'noreply@amce.org'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'body_html': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 14, 'style': 'font-size: 0.85rem;'}),
            'body_text': forms.Textarea(attrs={'class': 'form-control font-monospace', 'rows': 6, 'style': 'font-size: 0.85rem;'}),
        }


class EmailSettingsTestForm(forms.Form):
    test_recipient = forms.EmailField(
        required=True,
        label="Test Recipient Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g. your-email@amce.org'})
    )


