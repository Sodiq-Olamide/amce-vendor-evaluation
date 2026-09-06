from django.urls import path
from apps.evaluations import api_views

urlpatterns = [
    path('draft/', api_views.auto_save_draft_api, name='api_auto_save_draft'),
]
