from django.contrib import admin
from apps.evaluations.models import Submission, EvaluationResponse

class EvaluationResponseInline(admin.TabularInline):
    model = EvaluationResponse
    extra = 0
    fields = ('criterion', 'score', 'weighted_score', 'evidence_notes')
    readonly_fields = ('weighted_score',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('submission_id', 'evaluator', 'vendor', 'cohort', 'status', 'total_group_score', 'created_at')
    list_filter = ('status', 'vendor', 'cohort')
    search_fields = ('submission_id', 'evaluator__user__username', 'evaluator__user__first_name', 'evaluator__user__last_name')
    inlines = [EvaluationResponseInline]
    readonly_fields = ('record_hash', 'total_group_score')
