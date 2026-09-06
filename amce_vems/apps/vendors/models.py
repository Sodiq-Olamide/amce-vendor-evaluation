from django.db import models

class Vendor(models.Model):
    code = models.CharField(max_length=50, unique=True) # ezCareTech, ESI, SRIT, MEDITECH, KRANIUM
    name = models.CharField(max_length=255)
    lead_presenter = models.CharField(max_length=255, blank=True, null=True)
    solution_name = models.CharField(max_length=255)
    solution_version = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=50, blank=True, null=True)
    overview_description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
