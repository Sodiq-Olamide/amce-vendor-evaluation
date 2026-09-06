from decimal import Decimal
import pytest
from django.core.management import call_command
from apps.vendors.models import Vendor
from apps.forms_builder.models import EvaluationCohort, FormTemplate, CriterionQuestion
from apps.schedules.models import MasterCalendar
from apps.core.models import Department, EvaluatorProfile
from apps.evaluations.models import Submission, EvaluationResponse
from apps.analytics.services import ScoringEngineService

@pytest.fixture(autouse=True)
def seed_test_database(db):
    call_command('seed_evaluation_data')

@pytest.mark.django_db
class TestScoringAndEvaluationEngine:
    def test_cohort_weights_sum_to_100(self):
        cohorts = EvaluationCohort.objects.filter(is_active=True)
        total_weight = sum(c.default_weight for c in cohorts)
        assert total_weight == Decimal('100.00'), f"Cohort weights total {total_weight}%, expected 100%"

    def test_vendor_perfect_score_calculation(self):
        vendor = Vendor.objects.get(code='ezCareTech')
        evaluator = EvaluatorProfile.objects.first()
        calendar_slot = MasterCalendar.objects.first()

        # Score all 7 cohorts with 5.0 for ezCareTech
        cohorts = EvaluationCohort.objects.all()
        for ch in cohorts:
            template = FormTemplate.objects.filter(cohort=ch).first()
            sub, _ = Submission.objects.get_or_create(
                submission_id=f"TEST-PERFECT-{ch.slug}",
                evaluator=evaluator,
                calendar=calendar_slot,
                vendor=vendor,
                cohort=ch,
                template=template,
                status='SUBMITTED'
            )
            for crit in template.criteria.all():
                EvaluationResponse.objects.get_or_create(
                    submission=sub,
                    criterion=crit,
                    defaults={'score': Decimal('5.0'), 'evidence_notes': 'Exemplary quaternary demonstration verified.'}
                )
            sub.calculate_total_group_score()
            sub.save()

        # Calculate overall score for ezCareTech
        result = ScoringEngineService.calculate_vendor_overall_score(vendor)
        assert result['overall_score'] == 5.0, f"Expected 5.00 overall score, got {result['overall_score']}"

    def test_tie_breaking_order(self):
        matrix = ScoringEngineService.generate_executive_scorecard_matrix()
        assert len(matrix) == 5
        # Verify ordinal ranks 1 to 5
        ranks = [m['rank'] for m in matrix]
        assert ranks == [1, 2, 3, 4, 5]
