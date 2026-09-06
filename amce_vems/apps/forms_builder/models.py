from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User

class EvaluationCohort(models.Model):
    cohort_number = models.PositiveIntegerField(unique=True) # 1 to 7
    name = models.CharField(max_length=255) # Nursing Services, Oncology Services, etc.
    slug = models.SlugField(max_length=100, unique=True)
    default_weight = models.DecimalField(max_digits=5, decimal_places=2) # 15.00, 12.00, etc.
    target_audience = models.TextField()
    session_time_slot = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['cohort_number']

    def __str__(self):
        return f"{self.cohort_number}. {self.name} ({self.default_weight}%)"

class FormTemplate(models.Model):
    cohort = models.ForeignKey(EvaluationCohort, on_delete=models.RESTRICT, related_name='templates')
    version = models.CharField(max_length=20, default='1.0.0')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cohort', 'version')

    def __str__(self):
        return f"{self.title} (v{self.version})"

class CriterionQuestion(models.Model):
    template = models.ForeignKey(FormTemplate, on_delete=models.CASCADE, related_name='criteria')
    criterion_number = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    weight_percentage = models.DecimalField(max_digits=5, decimal_places=2) # e.g. 15.00, 20.00
    demo_prompt = models.TextField()
    guidance_notes = models.TextField(blank=True, null=True)
    requires_evidence_threshold = models.DecimalField(max_digits=3, decimal_places=1, default=Decimal('3.0'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['criterion_number']
        unique_together = ('template', 'criterion_number')

    def __str__(self):
        return f"[{self.template.cohort.name}] #{self.criterion_number}: {self.name} ({self.weight_percentage}%)"
