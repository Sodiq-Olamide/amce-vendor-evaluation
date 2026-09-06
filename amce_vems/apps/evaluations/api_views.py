import json
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.evaluations.models import Submission, EvaluationResponse
from apps.forms_builder.models import CriterionQuestion
from apps.audit.models import SystemAuditLog

@login_required
@require_POST
def auto_save_draft_api(request):
    """
    High-performance HTMX / Alpine JSON endpoint.
    Payload: { submission_id, criterion_id, score, evidence_notes }
    Returns: { status, criterion_weighted_score, total_group_score, saved_at }
    """
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        submission_id = data.get('submission_id')
        criterion_id = data.get('criterion_id')
        raw_score = data.get('score')
        notes = data.get('evidence_notes', '')

        submission = Submission.objects.get(
            submission_id=submission_id,
            evaluator__user=request.user
        )
        if submission.calendar.status == 'LOCKED':
            return JsonResponse({'status': 'error', 'message': f'Demonstration session for {submission.calendar.day_label} is LOCKED. Scores cannot be saved.'}, status=403)

        if submission.calendar.status != 'OPEN':
            return JsonResponse({'status': 'error', 'message': f'Evaluation session is currently {submission.calendar.get_status_display()}. Modifying scores is disabled.'}, status=403)

        if submission.status in ['SUBMITTED', 'MODERATED', 'LOCKED']:
            return JsonResponse({'status': 'error', 'message': 'Submission is locked against modifications.'}, status=403)

        criterion = CriterionQuestion.objects.get(id=criterion_id)
        score_val = Decimal(str(raw_score))

        resp_obj, created = EvaluationResponse.objects.get_or_create(
            submission=submission,
            criterion=criterion,
            defaults={'score': score_val, 'evidence_notes': notes}
        )
        if not created:
            resp_obj.score = score_val
            resp_obj.evidence_notes = notes
            resp_obj.save()

        # Recalculate submission total
        new_total = submission.calculate_total_group_score()
        submission.save(update_fields=['total_group_score', 'updated_at'])

        # Audit event
        SystemAuditLog.objects.create(
            user=request.user,
            action='AUTO_SAVE_DRAFT',
            entity_name='Submission',
            entity_id=str(submission.id),
            details={'criterion_id': criterion_id, 'score': str(score_val)}
        )

        return JsonResponse({
            'status': 'success',
            'criterion_weighted_score': f"{resp_obj.weighted_score:.4f}",
            'total_group_score': f"{new_total:.2f}",
            'saved_at': timezone.now().strftime('%H:%M:%S')
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
