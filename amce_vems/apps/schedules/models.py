from django.db import models
from apps.vendors.models import Vendor

class MasterCalendar(models.Model):
    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('OPEN', 'Open for Evaluation'),
        ('COMPLETED', 'Completed'),
        ('LOCKED', 'Locked / Sealed'),
    ]

    evaluation_date = models.DateField(unique=True)
    day_label = models.CharField(max_length=50) # 'Day 1', 'Day 2', etc.
    vendor = models.ForeignKey(Vendor, on_delete=models.RESTRICT, related_name='calendar_slots')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='OPEN')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['evaluation_date']

    def __str__(self):
        return f"{self.evaluation_date} ({self.day_label}) - {self.vendor.name} [{self.status}]"
