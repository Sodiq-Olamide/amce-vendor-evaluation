import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from apps.core.models import Department, EvaluatorProfile
from apps.vendors.models import Vendor
from apps.schedules.models import MasterCalendar
from apps.forms_builder.models import EvaluationCohort, FormTemplate, CriterionQuestion

class Command(BaseCommand):
    help = 'Seeds all authoritative master data: Vendors, Calendar, Cohorts, and 51 Criteria'

    def handle(self, *args, **options):
        self.stdout.write("Starting master data seeding from Excel baseline...")

        # 1. User Groups (RBAC)
        groups = ['Super Administrator', 'Evaluation Administrator', 'Evaluator', 'Executive Viewer']
        for g in groups:
            Group.objects.get_or_create(name=g)
        self.stdout.write(self.style.SUCCESS("[OK] RBAC Groups seeded."))

        # 2. Departments
        departments_data = [
            ('NURS', 'Nursing Services', 'Clinical'),
            ('ONC', 'Oncology Services', 'Clinical'),
            ('CARD', 'Cardiovascular Services', 'Clinical'),
            ('LAB', 'Laboratory Services and Blood Bank', 'Diagnostic'),
            ('RAD', 'Radiology and Nuclear Medicine', 'Diagnostic'),
            ('GENMED', 'General Medical & Surgical Services, and Pharmacy', 'Clinical'),
            ('ERP', 'ERP/RCM/Finance & Procurement', 'Administrative'),
        ]
        dept_map = {}
        for code, name, div in departments_data:
            dept, _ = Department.objects.get_or_create(code=code, defaults={'name': name, 'division': div})
            dept_map[name] = dept
        self.stdout.write(self.style.SUCCESS("[OK] Departments seeded."))

        # 3. Vendors
        vendors_data = [
            ('ezCareTech', 'ezCareTech', 'BESTCare 2.0 Quaternary Hospital Information System'),
            ('ESI', 'ESI', 'Enterprise Clinical Healthcare Suite'),
            ('SRIT', 'SRIT', 'Integrated Quaternary Hospital Management System'),
            ('MEDITECH', 'MEDITECH', 'MEDITECH Expanse Enterprise Healthcare Platform'),
            ('KRANIUM', 'KRANIUM', 'Kranium Clinical & Operational Suite'),
        ]
        vendor_map = {}
        for code, name, sol in vendors_data:
            vendor, _ = Vendor.objects.get_or_create(code=code, defaults={'name': name, 'solution_name': sol})
            vendor_map[name] = vendor
        self.stdout.write(self.style.SUCCESS("[OK] Vendors seeded."))

        # 4. Master Calendar (7-11 September 2026)
        calendar_data = [
            (datetime.date(2026, 9, 7), 'Day 1', 'ezCareTech'),
            (datetime.date(2026, 9, 8), 'Day 2', 'ESI'),
            (datetime.date(2026, 9, 9), 'Day 3', 'SRIT'),
            (datetime.date(2026, 9, 10), 'Day 4', 'MEDITECH'),
            (datetime.date(2026, 9, 11), 'Day 5', 'KRANIUM'),
        ]
        for dt, day, v_name in calendar_data:
            MasterCalendar.objects.get_or_create(
                evaluation_date=dt,
                defaults={'day_label': day, 'vendor': vendor_map[v_name], 'status': 'OPEN'}
            )
        self.stdout.write(self.style.SUCCESS("[OK] Master Calendar seeded."))

        # 5. Cohorts and Criteria
        cohorts_spec = [
            {
                'num': 1,
                'name': 'Nursing Services',
                'slug': 'nursing',
                'weight': Decimal('15.00'),
                'time_slot': '9:00 - 9:45 AM (WAT)',
                'audience': 'Nursing leadership and ward managers',
                'criteria': [
                    (1, 'Clinical documentation', Decimal('15.00'),
                     'Show a nurse completing a full shift assessment and vitals in under 3 taps/clicks, with mandatory fields enforced – not free text.'),
                    (2, 'Medication administration (drugs and infusion)', Decimal('15.00'),
                     'Demonstrate barcode/eMAR closed-loop administration: scan patient, scan drug, and show the system block a wrong-dose or wrong-patient attempt in real time.'),
                    (3, 'Care plans', Decimal('14.00'),
                     "Show a nursing care plan auto-suggested from the patient's diagnosis/risk score, editable by the nurse, and visible to the wider care team."),
                    (4, 'Orders', Decimal('14.00'),
                     'Show a nurse receiving, acknowledging and actioning a physician order (e.g. new IV) with a visible audit trail of who did what, when.'),
                    (5, 'Alerts/notifications', Decimal('14.00'),
                     'Trigger a critical alert (e.g. abnormal vital sign or allergy conflict) and show exactly how and where it reaches the nurse.'),
                    (6, 'Patient records', Decimal('14.00'),
                     "Pull one patient's full nursing record across two different encounters/wards in under 10 seconds."),
                    (7, 'Usability', Decimal('14.00'),
                     'Have a nurse who has never seen the system complete one full documentation task live, timed, with zero vendor prompting.'),
                ]
            },
            {
                'num': 2,
                'name': 'Oncology Services',
                'slug': 'oncology',
                'weight': Decimal('15.00'),
                'time_slot': '10:00 - 10:45 AM (WAT)',
                'audience': 'Oncologists, oncology nurses and relevant oncology clinical staff',
                'criteria': [
                    (1, 'Patient journey', Decimal('20.00'),
                     'Trace one oncology patient from first referral through diagnosis, staging and treatment start in a single continuous view.'),
                    (2, 'Treatment planning', Decimal('20.00'),
                     'Show a multidisciplinary tumour-board treatment plan being created, reviewed and signed off by more than one clinician role.'),
                    (3, 'Chemotherapy workflows and protocols', Decimal('20.00'),
                     'Demonstrate a protocol-driven chemo order with automatic dose calculation (e.g. BSA-based) and a hard stop on an out-of-range dose.'),
                    (4, 'Medication/order management', Decimal('20.00'),
                     'Show the verification chain for a chemotherapy order – pharmacist check, nurse check – before the drug can be administered.'),
                    (5, 'Documentation and follow-up', Decimal('20.00'),
                     'Show how a missed follow-up or overdue treatment cycle is flagged automatically, not manually tracked.'),
                ]
            },
            {
                'num': 3,
                'name': 'Cardiovascular Services',
                'slug': 'cardiology',
                'weight': Decimal('15.00'),
                'time_slot': '11:00 - 11:45 AM (WAT)',
                'audience': 'Cardiologists, cardiac nurses and relevant cardiac clinical staff',
                'criteria': [
                    (1, 'Clinical documentation', Decimal('20.00'),
                     'Show a cardiology consult note structured enough to auto-populate a discharge summary.'),
                    (2, 'Investigations', Decimal('20.00'),
                     'Order an ECG/Echo and show the result flow back into the same chart, not a separate silo.'),
                    (3, 'Orders', Decimal('10.00'),
                     'Show a cardiology order set (e.g. pre-cath workup) triggered as one bundle, not entered item by item.'),
                    (4, 'Procedures/surgeries', Decimal('20.00'),
                     'Show a cath-lab procedure note capturing device/stent details in structured, reportable fields.'),
                    (5, 'Results and follow-up', Decimal('10.00'),
                     'Show an abnormal result (e.g. critical troponin) triggering an immediate, trackable alert to the responsible clinician.'),
                    (6, 'Integration with cardiac monitors', Decimal('20.00'),
                     'Demonstrate a live or simulated feed from a cardiac monitor populating vitals directly into the record, with no manual re-entry. Confirm experience and capabilities to integrate.'),
                ]
            },
            {
                'num': 4,
                'name': 'Laboratory Services and Blood Bank',
                'slug': 'lab_blood',
                'weight': Decimal('15.00'),
                'time_slot': '12:00 - 12:45 PM (WAT)',
                'audience': 'Pathologists, laboratory scientists, laboratory management and relevant staff',
                'criteria': [
                    (1, 'Test ordering', Decimal('10.00'), 'Clinical order entry with collection container guidance, fasting rules, and specimen volume prompts.'),
                    (2, 'Specimen collection', Decimal('10.00'), 'Positive patient identification, bedside barcode tube printing, draw timestamps, and rejection workflows.'),
                    (3, 'Processing', Decimal('10.00'), "Show a specimen's status (received/in-process/complete) visible in real time to both lab and requesting clinician."),
                    (4, 'Validation', Decimal('10.00'), 'Show an out-of-range critical result being held for validation before it releases to the chart.'),
                    (5, 'Reporting', Decimal('15.00'), "Generate a final lab report and show it land directly in the patient's chart, formatted, not as a scanned PDF. Indicate template configuration and TAT/critical value reporting."),
                    (6, 'LIS functionality and interoperability', Decimal('10.00'), 'Show a bidirectional interface test: order goes out, result comes back, with no manual re-keying.'),
                    (7, 'Integration with lab equipment', Decimal('10.00'), 'Show at least one analyzer interface live – order-to-instrument and instrument-to-result. Present list of integrated analyzers.'),
                    (8, 'B2B', Decimal('10.00'), "Show how an external/referral lab's order is processed or result is ingested and reconciled against an AMCE order."),
                    (9, 'Blood Bank', Decimal('15.00'), 'Show the full blood-product chain: type & crossmatch, unit reservation, bedside two-person verification before transfusion.'),
                ]
            },
            {
                'num': 5,
                'name': 'Radiology and Nuclear Medicine',
                'slug': 'radiology',
                'weight': Decimal('12.00'),
                'time_slot': '2:00 - 2:45 PM (WAT)',
                'audience': 'Radiologist, Nuclear Medicine Consultants, Radiographers and Technicians',
                'criteria': [
                    (1, 'Investigation ordering', Decimal('25.00'), 'Order an imaging study with clinical indication captured as structured data, not free text.'),
                    (2, 'Reporting', Decimal('25.00'), "Show a radiologist dictating/finalising a report and it appearing in the ordering clinician's queue immediately."),
                    (3, 'Integration with RIS and PACS', Decimal('25.00'), 'Display integration capabilities and experiences. Show images and the report opening from a single click inside the same patient chart.'),
                    (4, 'B2B/Referrals', Decimal('25.00'), 'Show an external referral imaging study/report being received and matched to the correct AMCE patient record.'),
                ]
            },
            {
                'num': 6,
                'name': 'General Medical & Surgical Services, and Pharmacy',
                'slug': 'genmed_surg_pharm',
                'weight': Decimal('15.00'),
                'time_slot': '3:00 - 3:45 PM (WAT)',
                'audience': 'Clinicians, Surgeons, Pharmacists, and Technicians',
                'criteria': [
                    (1, 'Clinical documentation', Decimal('10.00'), 'Show a full admission note built from structured templates, not a blank text box.'),
                    (2, 'Investigations', Decimal('10.00'), 'Order labs/imaging from the same encounter and show results return to one unified timeline.'),
                    (3, 'Orders (incl. order sets & packages)', Decimal('10.00'), 'Trigger a pre-built order set (e.g. sepsis or pre-op bundle and wellness package) as a single action.'),
                    (4, 'Procedures/surgeries', Decimal('10.00'), 'Show the surgical safety checklist/time-out captured as a discrete, un-skippable step, not a note.'),
                    (5, 'Results and follow-up', Decimal('10.00'), 'Show an abnormal post-op result routed automatically to the responsible surgical team.'),
                    (6, 'Emergency workflow', Decimal('10.00'), 'Show a patient triaged and moved from ED registration to first clinical action, timestamped end to end.'),
                    (7, 'Prescription order, dispensing, reconciliation and reporting (incl. ADR, AMR, ABR, MDR)', Decimal('10.00'), 'Show a prescription flow from order to pharmacy dispense to bedside administration and reconciliation plus live ADR/AMR flagging.'),
                    (8, 'Patient Applications features and synchronization', Decimal('10.00'), 'Show a patient viewing their own results/appointments on the patient app, synced live with clinical record.'),
                    (9, 'Physician/Nursing Mobile Applications', Decimal('10.00'), 'Show a physician acting on an alert or order from a mobile device, not just viewing read-only data.'),
                    (10, 'AI integrations', Decimal('10.00'), 'Show one live AI-assisted feature (e.g. investigation review, documentation support, risk scoring) and its human-in-the-loop override.'),
                ]
            },
            {
                'num': 7,
                'name': 'ERP/RCM/Finance & Procurement',
                'slug': 'erp_finance',
                'weight': Decimal('13.00'),
                'time_slot': '4:00 - 4:45 PM (WAT)',
                'audience': 'Finance, Procurement, Supply Chain, Administration and relevant IT representatives',
                'criteria': [
                    (1, 'Billing', Decimal('15.00'), 'Generate a patient bill directly from clinical charges captured at point of care – no manual re-entry. Confirm auto-release for setup option.'),
                    (2, 'ERP integration', Decimal('10.00'), 'Show a clinical order automatically consuming inventory and hitting the general ledger in SAP. Exhibit profit centre distribution capabilities.'),
                    (3, 'Revenue cycle/package management', Decimal('10.00'), 'Show a bundled care package (e.g. a surgical package) priced and billed as one unit, with itemised detail available.'),
                    (4, 'Procurement workflow', Decimal('10.00'), 'Show a purchase requisition-to-PO-to-goods-receipt cycle with approval routing enforced, not bypassable.'),
                    (5, 'Inventory workflow', Decimal('10.00'), 'Show real-time stock visibility for a critical item and an automatic reorder trigger at a defined threshold.'),
                    (6, 'Finance workflow', Decimal('15.00'), 'Show a month-end close task with a clear audit trail of who approved what.'),
                    (7, 'Billing/revenue-cycle integration', Decimal('10.00'), 'Show insurance/NHIA claim data flowing from clinical encounter into claim submission without duplicate entry.'),
                    (8, 'Reporting', Decimal('10.00'), 'Pull one live financial or procurement report on demand, not a static export someone has to build offline.'),
                    (9, 'SAP integration', Decimal('10.00'), "Confirm and show, live, specific SAP S/4HANA Public Cloud modules you've integrated with, not on a roadmap."),
                ]
            },
        ]

        total_cohort_weight = Decimal('0.00')
        total_criteria_count = 0

        for c_data in cohorts_spec:
            cohort, _ = EvaluationCohort.objects.get_or_create(
                cohort_number=c_data['num'],
                defaults={
                    'name': c_data['name'],
                    'slug': c_data['slug'],
                    'default_weight': c_data['weight'],
                    'session_time_slot': c_data['time_slot'],
                    'target_audience': c_data['audience']
                }
            )
            total_cohort_weight += c_data['weight']

            template, _ = FormTemplate.objects.get_or_create(
                cohort=cohort,
                version='1.0.0',
                defaults={'title': f"AMCE HIS Vendor Evaluation Form – {cohort.name}"}
            )

            # Seed criteria
            c_weight_sum = Decimal('0.00')
            for c_num, c_name, c_wt, c_prompt in c_data['criteria']:
                CriterionQuestion.objects.get_or_create(
                    template=template,
                    criterion_number=c_num,
                    defaults={
                        'name': c_name,
                        'weight_percentage': c_wt,
                        'demo_prompt': c_prompt,
                    }
                )
                c_weight_sum += c_wt
                total_criteria_count += 1

            if c_weight_sum != Decimal('100.00'):
                self.stdout.write(self.style.WARNING(f"Warning: Cohort {cohort.name} criteria sum to {c_weight_sum}%, expected 100%"))

        self.stdout.write(self.style.SUCCESS(f"[OK] Seeded 7 Cohorts (Total weight: {total_cohort_weight}%) and {total_criteria_count} Criteria."))

        # 6. Seed Demo Evaluator & Admin Accounts
        admin_user, created = User.objects.get_or_create(username='admin', defaults={'email': 'admin@amce.ng', 'is_staff': True, 'is_superuser': True})
        if created:
            admin_user.set_password('AmceAdmin2026!')
            admin_user.save()
            admin_group = Group.objects.get(name='Super Administrator')
            admin_user.groups.add(admin_group)

        EvaluatorProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'employee_id': 'AMCE-ADM-001',
                'designation': 'System Administrator',
                'department': dept_map['Nursing Services']
            }
        )

        # Evaluator accounts matching Evaluator Master
        eval_demo, created = User.objects.get_or_create(
            username='evaluator01',
            defaults={'first_name': 'Amina', 'last_name': 'Bello', 'email': 'a.bello@amce.ng'}
        )
        if created:
            eval_demo.set_password('AmceEval2026!')
            eval_demo.save()
            eval_group = Group.objects.get(name='Evaluator')
            eval_demo.groups.add(eval_group)

        EvaluatorProfile.objects.get_or_create(
            user=eval_demo,
            defaults={
                'employee_id': 'AMCE-NUR-001',
                'designation': 'Nurse Manager - ICU & Inpatient',
                'department': dept_map['Nursing Services']
            }
        )

        # Executive Viewer
        exec_user, created = User.objects.get_or_create(
            username='executive',
            defaults={'first_name': 'Brian', 'last_name': 'Okonkwo', 'email': 'b.okonkwo@amce.ng'}
        )
        if created:
            exec_user.set_password('AmceExec2026!')
            exec_user.save()
            exec_group = Group.objects.get(name='Executive Viewer')
            exec_user.groups.add(exec_group)

        EvaluatorProfile.objects.get_or_create(
            user=exec_user,
            defaults={
                'employee_id': 'AMCE-EXE-001',
                'designation': 'Executive / Steering Committee',
                'department': dept_map['ERP/RCM/Finance & Procurement']
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Seeded Admin ('admin'), Evaluator ('evaluator01'), and Executive ('executive') accounts."))
        self.stdout.write(self.style.SUCCESS("Master Data Seeding Completed Successfully!"))
