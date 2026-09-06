import hashlib
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.core.models import EvaluatorProfile
from apps.vendors.models import Vendor
from apps.schedules.models import MasterCalendar
from apps.forms_builder.models import EvaluationCohort, FormTemplate, CriterionQuestion

class Submission(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft - In Progress'),
        ('SUBMITTED', 'Submitted - Awaiting Review'),
        ('MODERATED', 'Moderated - Department Approved'),
        ('LOCKED', 'Locked / Sealed'),
    ]

    submission_id = models.CharField(max_length=100, unique=True, db_index=True)
    evaluator = models.ForeignKey(EvaluatorProfile, on_delete=models.RESTRICT, related_name='submissions')
    calendar = models.ForeignKey(MasterCalendar, on_delete=models.RESTRICT, related_name='submissions')
    vendor = models.ForeignKey(Vendor, on_delete=models.RESTRICT, related_name='submissions')
    cohort = models.ForeignKey(EvaluationCohort, on_delete=models.RESTRICT, related_name='submissions')
    template = models.ForeignKey(FormTemplate, on_delete=models.RESTRICT, related_name='submissions')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT', db_index=True)
    total_group_score = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    general_notes = models.TextField(blank=True, null=True)
    
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    record_hash = models.CharField(max_length=64, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('evaluator', 'calendar', 'cohort')
        indexes = [
            models.Index(fields=['vendor', 'cohort', 'status']),
        ]

    def __str__(self):
        return f"{self.submission_id} | {self.evaluator.user.get_full_name() or self.evaluator.user.username} | {self.vendor.name}"

    def calculate_total_group_score(self):
        responses = self.responses.all()
        total = Decimal('0.0000')
        for r in responses:
            total += r.weighted_score
        self.total_group_score = total
        return self.total_group_score

    def generate_integrity_hash(self):
        responses = self.responses.order_by('criterion__criterion_number')
        digest_payload = f"{self.submission_id}|{self.evaluator_id}|{self.vendor_id}|"
        for r in responses:
            digest_payload += f"{r.criterion_id}:{r.score}:{r.evidence_notes}|"
        self.record_hash = hashlib.sha256(digest_payload.encode('utf-8')).hexdigest()
        return self.record_hash


class EvaluationResponse(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='responses')
    criterion = models.ForeignKey(CriterionQuestion, on_delete=models.RESTRICT, related_name='responses')
    score = models.DecimalField(max_digits=3, decimal_places=1) # 1.0 to 5.0
    weighted_score = models.DecimalField(max_digits=5, decimal_places=4)
    evidence_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('submission', 'criterion')

    def save(self, *args, **kwargs):
        weight_factor = self.criterion.weight_percentage / Decimal('100.0')
        self.weighted_score = self.score * weight_factor
        super().save(*args, **kwargs)
