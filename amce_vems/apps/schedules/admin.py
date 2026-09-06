from django.contrib import admin
from apps.schedules.models import MasterCalendar

@admin.register(MasterCalendar)
class MasterCalendarAdmin(admin.ModelAdmin):
    list_display = ('evaluation_date', 'day_label', 'vendor', 'status', 'created_at')
    list_filter = ('status', 'vendor')
    ordering = ('evaluation_date',)
