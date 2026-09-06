from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from apps.core.models import Department, EvaluatorProfile
from apps.core.forms import UserRoleAdminCreationForm, UserRoleAdminChangeForm

# Brand the admin site
admin.site.site_header = "AMCE HIS Vendor Evaluation Portal"
admin.site.site_title = "AMCE VEMS Administration"
admin.site.index_title = "System & User Management"

class EvaluatorProfileInline(admin.StackedInline):
    model = EvaluatorProfile
    can_delete = False
    verbose_name_plural = 'Hospital Role & Department Profile'
    fk_name = 'user'
    extra = 0
    fields = ('employee_id', 'designation', 'department', 'is_active')

# Unregister default UserAdmin
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """
    UI-Friendly UserAdmin with direct Role selection and automatic Profile management.
    """
    add_form = UserRoleAdminCreationForm
    form = UserRoleAdminChangeForm
    inlines = (EvaluatorProfileInline,)

    list_display = (
        'username',
        'get_full_name_display',
        'email',
        'role_badge',
        'get_department',
        'get_designation',
        'is_active',
        'date_joined'
    )
    list_filter = ('groups__name', 'is_active', 'evaluator_profile__department')
    search_fields = (
        'username',
        'first_name',
        'last_name',
        'email',
        'evaluator_profile__employee_id',
        'evaluator_profile__designation'
    )
    ordering = ('-date_joined',)
    actions = ['make_evaluator', 'make_executive', 'make_administrator']

    # Customize the "Add user" layout
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'first_name',
                'last_name',
                'email',
                'role',
                'department',
                'designation',
                'employee_id',
                'password1',
                'password2'
            ),
            'description': (
                "<strong>Fast User Onboarding</strong>: Choose an Account Role below. "
                "The system automatically provisions groups, permissions, and profile linkages."
            )
        }),
    )

    # Customize the "Edit user" layout
    fieldsets = (
        ('Account Credentials & Role', {
            'fields': ('username', 'password', 'role')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Hospital Profile Details', {
            'fields': ('department', 'designation', 'employee_id'),
            'description': "Evaluator & Executive profile properties."
        }),
        ('Access & Permissions', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {
            'classes': ('collapse',),
            'fields': ('last_login', 'date_joined')
        }),
    )

    @admin.display(description="Full Name")
    def get_full_name_display(self, obj):
        name = obj.get_full_name()
        return name if name.strip() else obj.username

    @admin.display(description="Account Role")
    def role_badge(self, obj):
        if obj.is_superuser or obj.groups.filter(name='Super Administrator').exists():
            return format_html(
                '<span style="background-color: #DBEAFE; color: #1E40AF; padding: 3px 8px; border-radius: 9999px; font-weight: 600; font-size: 0.75rem;">'
                '<i class="bi bi-shield-lock-fill"></i> Administrator</span>'
            )
        elif obj.groups.filter(name='Executive Viewer').exists():
            return format_html(
                '<span style="background-color: #D1FAE5; color: #065F46; padding: 3px 8px; border-radius: 9999px; font-weight: 600; font-size: 0.75rem;">'
                '<i class="bi bi-bar-chart-fill"></i> Executive</span>'
            )
        else:
            return format_html(
                '<span style="background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 9999px; font-weight: 600; font-size: 0.75rem;">'
                '<i class="bi bi-pencil-square"></i> Evaluator</span>'
            )

    @admin.display(description="Department")
    def get_department(self, obj):
        profile = getattr(obj, 'evaluator_profile', None)
        return profile.department.name if profile and profile.department else "—"

    @admin.display(description="Designation")
    def get_designation(self, obj):
        profile = getattr(obj, 'evaluator_profile', None)
        return profile.designation if profile else "—"

    # Quick Bulk Actions
    @admin.action(description="Convert selected users to Evaluator role")
    def make_evaluator(self, request, queryset):
        group, _ = Group.objects.get_or_create(name='Evaluator')
        for user in queryset:
            user.is_staff = False
            user.is_superuser = False
            user.save()
            user.groups.clear()
            user.groups.add(group)
        self.message_user(request, f"Updated {queryset.count()} user(s) to Evaluator role.")

    @admin.action(description="Convert selected users to Executive Viewer role")
    def make_executive(self, request, queryset):
        group, _ = Group.objects.get_or_create(name='Executive Viewer')
        for user in queryset:
            user.is_staff = False
            user.is_superuser = False
            user.save()
            user.groups.clear()
            user.groups.add(group)
        self.message_user(request, f"Updated {queryset.count()} user(s) to Executive Viewer role.")

    @admin.action(description="Promote selected users to System Administrator")
    def make_administrator(self, request, queryset):
        group, _ = Group.objects.get_or_create(name='Super Administrator')
        for user in queryset:
            user.is_staff = True
            user.is_superuser = True
            user.save()
            user.groups.clear()
            user.groups.add(group)
        self.message_user(request, f"Promoted {queryset.count()} user(s) to System Administrator.")


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'division', 'created_at')
    search_fields = ('code', 'name', 'division')
    list_filter = ('division',)
    ordering = ('code',)


@admin.register(EvaluatorProfile)
class EvaluatorProfileAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'designation', 'department', 'is_active', 'created_at')
    search_fields = ('employee_id', 'user__username', 'user__first_name', 'user__last_name', 'designation')
    list_filter = ('department', 'is_active')
    ordering = ('employee_id',)
