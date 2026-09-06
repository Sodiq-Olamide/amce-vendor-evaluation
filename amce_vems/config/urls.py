from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='base/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', include('apps.evaluations.urls')),
    path('executive/', include('apps.analytics.urls')),
    path('reports/', include('apps.reporting.urls')),
    path('management/', include('apps.core.urls')),
    path('api/v1/evaluations/', include('apps.evaluations.api_urls')),
]
