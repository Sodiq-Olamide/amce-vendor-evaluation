from django.contrib import admin
from apps.forms_builder.models import EvaluationCohort, FormTemplate, CriterionQuestion

class CriterionQuestionInline(admin.TabularInline):
    model = CriterionQuestion
    extra = 0
    fields = ('criterion_number', 'name', 'weight_percentage', 'demo_prompt')

@admin.register(EvaluationCohort)
class EvaluationCohortAdmin(admin.ModelAdmin):
    list_display = ('cohort_number', 'name', 'default_weight', 'session_time_slot', 'is_active')
    ordering = ('cohort_number',)

@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'cohort', 'version', 'is_published', 'created_at')
    inlines = [CriterionQuestionInline]
    list_filter = ('cohort', 'is_published')

@admin.register(CriterionQuestion)
class CriterionQuestionAdmin(admin.ModelAdmin):
    list_display = ('criterion_number', 'name', 'template', 'weight_percentage')
    list_filter = ('template__cohort',)
    search_fields = ('name', 'demo_prompt')
