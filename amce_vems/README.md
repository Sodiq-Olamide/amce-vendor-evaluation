# AMCE HIS Vendor Evaluation Management System (VEMS)

Production-ready Django web application for the **African Medical Centre of Excellence (AMCE) Abuja** to evaluate, score, consolidate, and rank Hospital Information System (HIS / EHR / ERP) vendors across clinical and non-clinical departments.

---

## Authoritative Baseline
- **Forms Prototype:** `AMCE_HIS_Vendor_Evaluation_Forms_Prototype.xlsx`
- **Consolidated Scoring Model:** `HIS_Vendor_Evaluation_Scoring_Sheet.xlsx`
- **Enterprise Architectural Blueprint:** `AMCE_HIS_Vendor_Evaluation_Enterprise_Blueprint.md`

---

## 5-Day Demonstration Schedule & Vendor Roster
- **Day 1 (Monday, 07-Sep-2026):** `ezCareTech`
- **Day 2 (Tuesday, 08-Sep-2026):** `ESI`
- **Day 3 (Wednesday, 09-Sep-2026):** `SRIT`
- **Day 4 (Thursday, 10-Sep-2026):** `MEDITECH`
- **Day 5 (Friday, 11-Sep-2026):** `KRANIUM`

---

## 7 Evaluation User Groups & Calibrated Weights
1. **Nursing Services:** `15.0%` (7 Criteria)
2. **Oncology Services:** `15.0%` (5 Criteria)
3. **Cardiovascular Services:** `15.0%` (6 Criteria)
4. **Laboratory Services & Blood Bank:** `15.0%` (9 Criteria)
5. **Radiology & Nuclear Medicine:** `12.0%` (4 Criteria)
6. **General Medical & Surgical Services, and Pharmacy:** `15.0%` (10 Criteria)
7. **ERP/RCM/Finance & Procurement:** `13.0%` (9 Criteria)
- **Total Weight Check:** Exactly `100.0%`

---

## Local Development Setup

### 1. Prerequisites
- Python 3.12+ / 3.14
- Virtual environment or global Python runtime

### 2. Quickstart
```bash
# Navigate to project directory
cd amce_vems

# Install dependencies
pip install -r requirements.txt

# Run migrations (defaults to local SQLite if DATABASE_URL is not set)
python manage.py migrate

# Seed all 5 vendors, calendar, 7 cohorts, 51 criteria, and demo accounts
python manage.py seed_evaluation_data

# Start development server
python manage.py runserver
```

Open your browser at: `http://localhost:8000/`

### 3. Demo Credentials
- **Evaluator:** Username `evaluator01` | Password `AmceEval2026!`
- **Executive Viewer:** Username `executive` | Password `AmceExec2026!`
- **Super Administrator:** Username `admin` | Password `AmceAdmin2026!`

---

## Automated Test Suite
Run the automated test suite verifying mathematical rollup precision, weight invariants, and ranking engines:
```bash
cd amce_vems
python -m pytest
```

---

## Railway.app Deployment Guide

The codebase is pre-configured for one-click deployment on [Railway.app](https://railway.app).

### 1. Add Repository to Railway
1. Push this repository to GitHub or upload via Railway CLI.
2. In Railway Dashboard, select **New Project** ➔ **Deploy from GitHub repo**.

### 2. Add PostgreSQL Plugin
1. Click **+ New** ➔ **Database** ➔ **Add PostgreSQL**.
2. Railway automatically provisions PostgreSQL and sets the `DATABASE_URL` environment variable.

### 3. Environment Variables
In Railway service settings, configure:
- `DJANGO_SETTINGS_MODULE`: `config.settings.base`
- `SECRET_KEY`: `[secure random string]`
- `DEBUG`: `0`
- `ALLOWED_HOSTS`: `.railway.app,localhost`
- `CSRF_TRUSTED_ORIGINS`: `https://*.railway.app`

### 4. Automated Build & Start Commands
`railway.json` and `Procfile` are pre-packaged:
- Automatic migrations: `python manage.py migrate --noinput`
- Static collection: `python manage.py collectstatic --noinput`
- Master data seeding: `python manage.py seed_evaluation_data`
- Web server: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
