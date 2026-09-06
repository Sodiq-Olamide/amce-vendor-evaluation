from django.urls import path
from apps.reporting import views

urlpatterns = [
    path('export/excel/', views.export_scorecard_excel, name='export_scorecard_excel'),
]
