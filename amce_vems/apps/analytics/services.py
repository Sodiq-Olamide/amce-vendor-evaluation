from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Avg
from apps.vendors.models import Vendor
from apps.forms_builder.models import EvaluationCohort
from apps.evaluations.models import Submission, EvaluationResponse

class ScoringEngineService:
    @classmethod
    def calculate_vendor_cohort_score(cls, vendor: Vendor, cohort: EvaluationCohort) -> Decimal:
        """
        Computes the consensus score (out of 5.00) for a vendor in a specific cohort.
        Averages evaluator group scores across valid SUBMITTED, MODERATED, or LOCKED records.
        """
        submissions = Submission.objects.filter(
            vendor=vendor,
            cohort=cohort,
            status__in=['SUBMITTED', 'MODERATED', 'LOCKED']
        )
        if not submissions.exists():
            return Decimal('0.0000')
        
        avg_score = submissions.aggregate(avg=Avg('total_group_score'))['avg']
        if avg_score is None:
            return Decimal('0.0000')
        return Decimal(str(avg_score)).quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)

    @classmethod
    def calculate_vendor_overall_score(cls, vendor: Vendor, custom_weights_map: dict = None) -> dict:
        """
        Calculates the complete enterprise weighted rollup across all 7 cohorts.
        Overall Score = Sum( DepartmentScore_i * (CohortWeight_i / 100) )
        """
        cohorts = EvaluationCohort.objects.filter(is_active=True).order_by('cohort_number')
        cohort_breakdown = {}
        total_overall_score = Decimal('0.0000')
        
        for ch in cohorts:
            dept_score = cls.calculate_vendor_cohort_score(vendor, ch)
            
            # Allow custom weights for executive sensitivity "what-if" simulations
            if custom_weights_map and ch.slug in custom_weights_map:
                weight = Decimal(str(custom_weights_map[ch.slug]))
            else:
                weight = ch.default_weight

            weight_factor = weight / Decimal('100.0')
            weighted_contrib = dept_score * weight_factor
            
            cohort_breakdown[ch.slug] = {
                'cohort_id': ch.id,
                'cohort_name': ch.name,
                'weight_percentage': float(weight),
                'raw_score': float(dept_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'weighted_contribution': float(weighted_contrib.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)),
            }
            total_overall_score += weighted_contrib

        final_score_2dp = total_overall_score.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return {
            'vendor_id': vendor.id,
            'vendor_code': vendor.code,
            'vendor_name': vendor.name,
            'solution_name': vendor.solution_name,
            'overall_score': float(final_score_2dp),
            'overall_score_raw': float(total_overall_score),
            'breakdown': cohort_breakdown
        }

    @classmethod
    def generate_executive_scorecard_matrix(cls, custom_weights_map: dict = None) -> list:
        """
        Generates the consolidated 5-vendor comparison matrix and computes ordinal ranks.
        Applies deterministic clinical tie-breaking hierarchy.
        """
        vendors = Vendor.objects.filter(is_active=True)
        results = [cls.calculate_vendor_overall_score(v, custom_weights_map) for v in vendors]
        
        # Tie-breaker key: 
        # 1. overall_score_raw desc
        # 2. Clinical score sum (nursing + oncology + cardiology + genmed) desc
        # 3. lab_blood score desc
        # 4. erp_finance score desc
        def sort_key(item):
            b = item['breakdown']
            clinical_sum = (
                b.get('nursing', {}).get('raw_score', 0) +
                b.get('oncology', {}).get('raw_score', 0) +
                b.get('cardiology', {}).get('raw_score', 0) +
                b.get('genmed_surg_pharm', {}).get('raw_score', 0)
            )
            lab_score = b.get('lab_blood', {}).get('raw_score', 0)
            erp_score = b.get('erp_finance', {}).get('raw_score', 0)
            return (item['overall_score_raw'], clinical_sum, lab_score, erp_score)

        results.sort(key=sort_key, reverse=True)
        
        for rank_idx, item in enumerate(results, start=1):
            item['rank'] = rank_idx
            
        return results
