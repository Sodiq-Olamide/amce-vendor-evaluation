from django.urls import path
from apps.core import views

urlpatterns = [
    # Hub
    path('', views.admin_hub, name='admin_hub'),

    # Users
    path('users/', views.user_management_list, name='user_management_list'),
    path('users/new/', views.user_create_view, name='user_create'),
    path('users/from-ad/', views.user_provision_from_ad, name='user_provision_from_ad'),
    path('users/ad-lookup/', views.ad_user_lookup_api, name='ad_user_lookup_api'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user_edit'),
    path('users/<int:user_id>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:user_id>/set-role/', views.user_set_role, name='user_set_role'),
    path('users/<int:user_id>/toggle-perm/', views.user_toggle_permission, name='user_toggle_permission'),
    path('groups/<int:group_id>/toggle-perm/', views.group_permission_toggle, name='group_permission_toggle'),

    # Vendors
    path('vendors/', views.admin_vendor_list, name='admin_vendor_list'),
    path('vendors/new/', views.admin_vendor_create, name='admin_vendor_create'),
    path('vendors/<int:vendor_id>/edit/', views.admin_vendor_edit, name='admin_vendor_edit'),
    path('vendors/<int:vendor_id>/toggle/', views.admin_vendor_toggle, name='admin_vendor_toggle'),

    # Master Calendar & Schedules
    path('schedules/', views.admin_calendar_list, name='admin_calendar_list'),
    path('schedules/new/', views.admin_calendar_create, name='admin_calendar_create'),
    path('schedules/<int:slot_id>/edit/', views.admin_calendar_edit, name='admin_calendar_edit'),
    path('schedules/<int:slot_id>/status/', views.admin_calendar_set_status, name='admin_calendar_set_status'),

    # Cohorts & Criteria Form Builder
    path('cohorts/', views.admin_cohorts_list, name='admin_cohorts_list'),
    path('cohorts/<int:cohort_id>/edit/', views.admin_cohort_edit, name='admin_cohort_edit'),
    path('cohorts/<int:cohort_id>/criteria/', views.admin_cohort_criteria, name='admin_cohort_criteria'),
    path('cohorts/<int:cohort_id>/criteria/new/', views.admin_criterion_create, name='admin_criterion_create'),
    path('cohorts/<int:cohort_id>/criteria/<int:criterion_id>/edit/', views.admin_criterion_edit, name='admin_criterion_edit'),

    # Submissions Moderation, Lockdown & Official Scorecard Printout
    path('submissions/', views.admin_submissions_list, name='admin_submissions_list'),
    path('submissions/print-all/', views.admin_submissions_print_all, name='admin_submissions_print_all'),
    path('submissions/export-all/excel/', views.admin_submissions_export_all_excel, name='admin_submissions_export_all_excel'),
    path('submissions/<str:submission_id>/toggle-lock/', views.admin_submission_toggle_lock, name='admin_submission_toggle_lock'),
    path('submissions/<str:submission_id>/print/', views.admin_submission_printout, name='admin_submission_printout'),

    # Dynamic Message Templates, Email Setup & Notification Logs
    path('messages/templates/', views.admin_email_templates_list, name='admin_email_templates_list'),
    path('messages/templates/<int:template_id>/edit/', views.admin_email_template_edit, name='admin_email_template_edit'),
    path('messages/templates/<int:template_id>/preview/', views.admin_email_template_preview, name='admin_email_template_preview'),
    path('messages/setup/', views.admin_email_settings_view, name='admin_email_settings'),
    path('messages/logs/', views.admin_email_logs_list, name='admin_email_logs_list'),
]


