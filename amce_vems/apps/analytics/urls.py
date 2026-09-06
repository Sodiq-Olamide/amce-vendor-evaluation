from django.urls import path
from apps.analytics import views

urlpatterns = [
    path('', views.executive_dashboard_view, name='executive_dashboard'),
    path('api/simulate/', views.sensitivity_simulator_api, name='api_sensitivity_simulator'),
]
