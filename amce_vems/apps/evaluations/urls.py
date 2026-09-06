from django.urls import path
from apps.evaluations import views

urlpatterns = [
    path('', views.active_session_redirect, name='home_redirect'),
    path('evaluator/', views.evaluator_dashboard, name='evaluator_dashboard'),
    path('scorecard/<slug:cohort_slug>/', views.scorecard_view, name='scorecard_view'),
    path('submission/<str:submission_id>/finalize/', views.finalize_submission, name='finalize_submission'),
]
