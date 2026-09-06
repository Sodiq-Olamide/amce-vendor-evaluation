# AMCE HIS Vendor Evaluation Management System (VEMS) - Walkthrough

The complete enterprise Django web application for the **African Medical Centre of Excellence (AMCE) Abuja** has been constructed, validated locally, and configured for seamless deployment to **Railway.app**.

---

## 1. Accomplishments & Delivered Components

### 1.1 Authoritative Master Data & Seeding (`amce_vems/apps/core/management/commands/seed_evaluation_data.py`)
All master entities from `AMCE_HIS_Vendor_Evaluation_Forms_Prototype.xlsx` and `HIS_Vendor_Evaluation_Scoring_Sheet.xlsx` have been codified into the database:
- **5 HIS Vendors:** `ezCareTech`, `ESI`, `SRIT`, `MEDITECH`, `KRANIUM`.
- **Master Demonstration Calendar:** Day 1 (07-Sep) through Day 5 (11-Sep-2026) with automatic vendor-by-date binding.
- **7 Evaluation Cohorts:**
  - *Nursing Services:* 15% (7 Criteria)
  - *Oncology Services:* 15% (5 Criteria)
  - *Cardiovascular Services:* 15% (6 Criteria)
  - *Laboratory Services & Blood Bank:* 15% (9 Criteria)
  - *Radiology & Nuclear Medicine:* 12% (4 Criteria)
  - *General Medical & Surgical Services, and Pharmacy:* 15% (10 Criteria)
  - *ERP/RCM/Finance & Procurement:* 13% (9 Criteria)
  - **Total Enterprise Weight:** Exactly **100.00%**.
- **All 51 Demonstration Criteria:** Complete titles, weights, demo prompts, and guidance notes.
- **RBAC Roles & Demo Profiles:** Seeded `admin`, `evaluator01` (Amina Bello, Nurse Manager ICU), and `executive` (Brian Okonkwo).

---

### 1.2 Mathematical Scoring Engine (`amce_vems/apps/analytics/services.py`)
- **Level 1 (Criterion Score):** $S_{ijk} \in [1.0, 5.0]$
- **Level 2 (Individual Weighted Score):** $\sum (S_{ijk} \times \frac{w_{ik}}{100})$
- **Level 3 (Department Consensus):** Averaged across valid submissions for that cohort.
- **Level 4 (Enterprise Overall Score):** Weighted sum across all 7 cohorts using the master percentage weights.
- **Level 5 (Tie-Breaker Hierarchy):** 
  1. Highest overall raw score
  2. Highest clinical score sum (Nursing + Oncology + Cardiology + GenMed)
  3. Highest Laboratory/Blood Bank score
  4. Highest ERP/Finance score.
- **Executive Sensitivity Simulator:** Instant "What-If" cohort weight adjustment without database mutation.

---

### 1.3 Interactive Evaluator Scorecard UI (`amce_vems/templates/evaluations/scorecard.html`)
- Automatic resolution of evaluator identity, department, designation, and scheduled vendor.
- **Alpine.js Real-Time Calculation:** Weighted criterion score and total group score recalculate smoothly on-screen as rating pills are tapped.
- **Background Auto-Save Endpoint:** Asynchronous JSON/HTMX API (`/api/v1/evaluations/draft/`) auto-saving ratings and qualitative evidence.
- **Mandatory Notes Threshold:** Visual warning and validation blocker enforcing a minimum 20-character qualitative explanation if score $\le 2.5$ or $= 5.0$.
- **Session Finalization & SHA-256 Seal:** Computes cryptographic digest across all response rows, locking the scorecard against subsequent edits.

---

### 1.4 Executive Decision-Support Dashboard (`amce_vems/templates/executive/dashboard.html`)
- **Consolidated 5-Vendor Matrix:** Real-time heatmap table displaying all 7 cohorts, overall scores out of 5.00, and official ranks.
- **Multi-Vendor Radar Spider Chart (Chart.js):** Overlays all 5 vendor performance envelopes across the 7 cohort axes.
- **Live Sensitivity Simulator:** Executive slider panel with automatic sum-check (100%) and instant simulated re-ranking.
- **High-Fidelity Excel Export (`/reports/export/excel/`):** Produces a fully formatted `.xlsx` workbook using openpyxl matching the prototype summary scorecard.

---

## 2. Validation & Testing Results

### 2.1 Automated Test Suite (`python -m pytest`)
The automated test suite executed with **100% passing rate**:
```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
django: version: 6.0.5, settings: config.settings.base (from ini)
rootdir: C:\...\amce_vems
configfile: pytest.ini
plugins: django-4.14.0
collected 3 items

tests\test_scoring.py ...                                                [100%]

============================== 3 passed in 6.15s ==============================
```
- `test_cohort_weights_sum_to_100`: Verified exact 100.00% sum invariant.
- `test_vendor_perfect_score_calculation`: Verified that all 5.0 ratings compute to an overall score of exactly 5.00.
- `test_tie_breaking_order`: Verified ordinal ranking and tie-breaking algorithms.

### 2.2 View Execution & HTTP Status Verification
- `Executive Dashboard (/executive/)`: HTTP **200 OK**
- `Evaluator Dashboard (/evaluator/)`: HTTP **200 OK**
- `Nursing Scorecard (/scorecard/nursing/)`: HTTP **200 OK**
- `Excel Export (/reports/export/excel/)`: HTTP **200 OK**, Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` (6,021 bytes valid Excel file).

---

## 3. How to Run Locally

```bash
cd "c:\Users\sambali\OneDrive - AFRICAN MEDICAL CENTRE OF EXCELLENCE\Documents\Application Support\AMCE Vendor Evaluation\amce_vems"
python manage.py runserver
```
Visit `http://localhost:8000/` and sign in with:
- **Evaluator:** `evaluator01` / `AmceEval2026!`
- **Executive Viewer:** `executive` / `AmceExec2026!`
- **Super Admin:** `admin` / `AmceAdmin2026!`

---

## 4. Railway Deployment Configuration
All necessary deployment files have been generated:
- `amce_vems/railway.json`: Automatic migrations, static collection, seeding, and Gunicorn start command.
- `amce_vems/Procfile`: `web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
- `amce_vems/docker/Dockerfile` & `amce_vems/docker/docker-compose.yml`: Multi-container containerization for local or production Docker environments.
- `config/settings/base.py`: Auto-detects Railway's `DATABASE_URL` for PostgreSQL while running SQLite locally with zero configuration.
