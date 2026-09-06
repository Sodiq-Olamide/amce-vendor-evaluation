import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from apps.analytics.services import ScoringEngineService
from apps.forms_builder.models import EvaluationCohort
from apps.vendors.models import Vendor

def can_access_export_excel(user):
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff or user.groups.filter(name__in=['Super Administrator', 'Executive Viewer']).exists():
        return True
    return user.has_perm('analytics.can_export_scorecard_excel')

@login_required
@user_passes_test(can_access_export_excel)
def export_scorecard_excel(request):

    """
    Generates a high-fidelity .xlsx export mirroring the authoritative Excel prototype.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary Scorecard"

    # Styling definitions
    navy_fill = PatternFill(start_color="0B2545", end_color="0B2545", fill_type="solid")
    teal_fill = PatternFill(start_color="139A8C", end_color="139A8C", fill_type="solid")
    gold_fill = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid")
    gray_fill = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")

    white_bold = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    navy_bold = Font(name="Calibri", size=12, bold=True, color="0B2545")
    title_font = Font(name="Calibri", size=14, bold=True, color="0B2545")
    regular_font = Font(name="Calibri", size=11)
    bold_font = Font(name="Calibri", size=11, bold=True)

    thin_border = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )

    # Title Banner
    ws.merge_cells("A1:G1")
    ws["A1"] = "HIS Vendor Evaluation - Summary Scorecard"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")

    ws.merge_cells("A2:G2")
    ws["A2"] = "African Medical Centre of Excellence (AMCE) Abuja - Comparative Vendor Demonstration Programme"
    ws["A2"].font = Font(name="Calibri", size=11, italic=True, color="475569")

    ws.merge_cells("A3:G3")
    ws["A3"] = "Weighted score (out of 5) per cohort. Group weights: Nursing 15%, Oncology 15%, Cardiology 15%, Lab 15%, Radiology 12%, GenMed 15%, ERP 13%."
    ws["A3"].font = Font(name="Calibri", size=10, italic=True, color="64748B")

    # Header Row
    headers = ["Cohort / User Group", "Group Weight (%)", "ezCareTech", "ESI", "SRIT", "MEDITECH", "KRANIUM"]
    ws.append([])
    ws.append(headers)
    header_row_idx = 5
    for col_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=header_row_idx, column=col_idx)
        cell.font = white_bold
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center" if col_idx > 1 else "left", vertical="center")
        cell.border = thin_border

    matrix = ScoringEngineService.generate_executive_scorecard_matrix()
    cohorts = EvaluationCohort.objects.filter(is_active=True).order_by('cohort_number')
    
    # Map vendor code to matrix item
    v_map = {m['vendor_code']: m for m in matrix}

    # Data Rows
    current_row = 6
    for ch in cohorts:
        row_cells = [ch.name, float(ch.default_weight)]
        for v_code in ["ezCareTech", "ESI", "SRIT", "MEDITECH", "KRANIUM"]:
            v_data = v_map.get(v_code, {})
            score = v_data.get('breakdown', {}).get(ch.slug, {}).get('raw_score', 0.0)
            row_cells.append(score)
        
        ws.append(row_cells)
        for c_idx in range(1, len(row_cells) + 1):
            cell = ws.cell(row=current_row, column=c_idx)
            cell.font = regular_font
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center" if c_idx > 1 else "left", vertical="center")
        current_row += 1

    # Total Weight Check Row
    ws.append(["Weight check (should equal 100%)", 100, "", "", "", "", ""])
    ws.cell(row=current_row, column=1).font = bold_font
    ws.cell(row=current_row, column=2).font = bold_font
    current_row += 1

    # Overall Weighted Score Row
    overall_scores = ["OVERALL WEIGHTED SCORE (out of 5)", ""]
    for v_code in ["ezCareTech", "ESI", "SRIT", "MEDITECH", "KRANIUM"]:
        overall_scores.append(v_map.get(v_code, {}).get('overall_score', 0.0))
    ws.append(overall_scores)
    for c_idx in range(1, len(overall_scores) + 1):
        cell = ws.cell(row=current_row, column=c_idx)
        cell.font = white_bold
        cell.fill = teal_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center" if c_idx > 1 else "left", vertical="center")
    current_row += 1

    # Rank Row
    ranks = ["RANK", ""]
    for v_code in ["ezCareTech", "ESI", "SRIT", "MEDITECH", "KRANIUM"]:
        ranks.append(v_map.get(v_code, {}).get('rank', 0))
    ws.append(ranks)
    for c_idx in range(1, len(ranks) + 1):
        cell = ws.cell(row=current_row, column=c_idx)
        cell.font = white_bold
        cell.fill = gold_fill
        cell.border = thin_border
        cell.alignment = Alignment(horizontal="center" if c_idx > 1 else "left", vertical="center")

    # Column dimensions auto-adjust
    ws.column_dimensions['A'].width = 50
    ws.column_dimensions['B'].width = 18
    for col_letter in ['C', 'D', 'E', 'F', 'G']:
        ws.column_dimensions[col_letter].width = 16

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="AMCE_HIS_Vendor_Evaluation_Summary.xlsx"'
    return response
