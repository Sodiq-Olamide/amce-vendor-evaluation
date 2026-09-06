from django.contrib import admin
from apps.vendors.models import Vendor

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'solution_name', 'is_active', 'created_at')
    search_fields = ('code', 'name', 'solution_name')
    list_filter = ('is_active',)
    ordering = ('code',)
