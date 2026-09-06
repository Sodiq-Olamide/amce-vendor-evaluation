import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="{top}" w:type="dxa"/>
            <w:bottom w:w="{bottom}" w:type="dxa"/>
            <w:left w:w="{left}" w:type="dxa"/>
            <w:right w:w="{right}" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

def add_code_block(doc, code_text):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Inches(6.5)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, "F8FAFC")
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    
    run = p.add_run(code_text.strip())
    run.font.name = 'Consolas'
    run.font.size = Pt(9.5)
    run.font.color.rgb = RGBColor(30, 41, 59)
    
    # Empty space after table
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def add_callout(doc, text, title="IMPORTANT NOTICE", border_hex="0B2545", bg_hex="F1F5F9"):
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.columns[0].width = Inches(6.5)
    
    cell = table.cell(0, 0)
    set_cell_background(cell, bg_hex)
    set_cell_margins(cell, top=140, bottom=140, left=180, right=180)
    
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    
    r_title = p.add_run(f"[{title}] ")
    r_title.font.name = 'Segoe UI'
    r_title.font.bold = True
    r_title.font.size = Pt(10)
    r_title.font.color.rgb = RGBColor(11, 37, 69)
    
    r_text = p.add_run(text)
    r_text.font.name = 'Segoe UI'
    r_text.font.size = Pt(9.5)
    r_text.font.color.rgb = RGBColor(51, 65, 85)
    
    sp = doc.add_paragraph()
    sp.paragraph_format.space_before = Pt(0)
    sp.paragraph_format.space_after = Pt(6)

def create_document(output_path):
    doc = Document()
    
    # Page setup - Normal 1 inch margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    # Styles
    navy = RGBColor(11, 37, 69)     # #0B2545
    teal = RGBColor(19, 154, 140)   # #139A8C
    slate = RGBColor(71, 85, 105)   # #475569
    dark = RGBColor(30, 41, 59)     # #1E293B

    # Document Header Title
    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_before = Pt(0)
    title_p.paragraph_format.space_after = Pt(2)
    r_sub = title_p.add_run("AFRICAN MEDICAL CENTRE OF EXCELLENCE (AMCE) ABUJA\n")
    r_sub.font.name = 'Segoe UI'
    r_sub.font.bold = True
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = teal
    
    r_main = title_p.add_run("Production Deployment & Infrastructure Engineering Guide\n")
    r_main.font.name = 'Segoe UI Semibold'
    r_main.font.bold = True
    r_main.font.size = Pt(22)
    r_main.font.color.rgb = navy
    
    r_desc = title_p.add_run("AMCE Vendor Evaluation Management System (VEMS) - Full Operational Blueprint")
    r_desc.font.name = 'Segoe UI'
    r_desc.font.italic = True
    r_desc.font.size = Pt(12)
    r_desc.font.color.rgb = slate
    
    # Meta Info Table
    meta_table = doc.add_table(rows=2, cols=2)
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_table.columns[0].width = Inches(3.25)
    meta_table.columns[1].width = Inches(3.25)
    
    cells = meta_table.rows[0].cells
    cells[0].text = "System: AMCE VEMS Enterprise"
    cells[1].text = "Target Environments: Railway PaaS & On-Premises Windows VM"
    cells = meta_table.rows[1].cells
    cells[0].text = "Version: 1.0 Production Candidate"
    cells[1].text = "Scope: Complete Architecture, Settings, Commands & Configurations"
    
    for row in meta_table.rows:
        for cell in row.cells:
            set_cell_background(cell, "F1F5F9")
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            p = cell.paragraphs[0]
            p.runs[0].font.name = 'Segoe UI'
            p.runs[0].font.size = Pt(9)
            p.runs[0].font.color.rgb = slate
            
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # --- EXECUTIVE SUMMARY ---
    h1 = doc.add_heading(level=1)
    h1_r = h1.add_run("1. Architectural Overview & Environment Strategy")
    h1_r.font.name = 'Segoe UI'
    h1_r.font.bold = True
    h1_r.font.color.rgb = navy
    
    p = doc.add_paragraph(
        "This guide provides comprehensive, non-abbreviated operational blueprints for transitioning the "
        "AMCE Vendor Evaluation Management System (VEMS) into production across two enterprise deployment architectures:\n"
        "• Deployment Option 1: Managed Cloud Platform-as-a-Service (Railway.app) with Managed PostgreSQL, automated TLS, and Git CI/CD.\n"
        "• Deployment Option 2: On-Premises Microsoft Windows Server VM (Hyper-V / VMware / Azure VM) with IIS Reverse Proxy, "
        "PostgreSQL 16, NSSM Windows Service daemon, and native Windows Active Directory (LDAP/LDAPS) connectivity."
    )
    p.paragraph_format.line_spacing = 1.2
    
    # --- SETTINGS FILE REFACTORING ---
    h1 = doc.add_heading(level=1)
    h1_r = h1.add_run("2. Core Settings Architecture: What Must Be Edited")
    h1_r.font.name = 'Segoe UI'
    h1_r.font.bold = True
    h1_r.font.color.rgb = navy
    
    p = doc.add_paragraph(
        "The project settings reside inside `amce_vems/config/settings/base.py`. In a secure production environment, "
        "hardcoded secrets must never be used, DEBUG must be set to False, ALLOWED_HOSTS must restrict host headers, "
        "CSRF_TRUSTED_ORIGINS must include the production domain, and HTTPS security headers must be enforced."
    )
    
    doc.add_heading(level=2).add_run("2.1 Exact Settings Verification in base.py").font.color.rgb = navy
    p = doc.add_paragraph(
        "Ensure `config/settings/base.py` accurately contains the following environment variable readers. "
        "Notice that our configuration natively adapts based on whether `DATABASE_URL` is passed (PostgreSQL on Railway/VM) "
        "or falls back to SQLite for local development:"
    )
    
    code_base_py = """# config/settings/base.py (Security & Production Essentials)

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 1. Environment Variable Loader (.env / env.txt)
env_candidates = [
    BASE_DIR / '.env',
    BASE_DIR.parent / '.env',
    BASE_DIR / 'env.txt',
    BASE_DIR.parent / 'env.txt',
]
for env_path in env_candidates:
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v

# 2. Production Security Controls
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError("CRITICAL: SECRET_KEY environment variable is not set!")

DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')

ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',') if h.strip()]

CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1:8000').split(',') if o.strip()]

# 3. HTTPS Strict Security Headers (Enforced when DEBUG=False)
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 't')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 Year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# 4. Enterprise Dual Database Setup
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    url = urlparse(DATABASE_URL)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port or 5432,
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# 5. Production Mail Delivery Subsystem
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.office365.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'AMCE Vendor Evaluation <noreply@amce.ng>')
SITE_DOMAIN = os.environ.get('SITE_DOMAIN', 'https://vems.amce.ng')
"""
    add_code_block(doc, code_base_py)
    
    # --- OPTION 1: RAILWAY PAAS ---
    h1 = doc.add_heading(level=1)
    h1_r = h1.add_run("3. Deployment Option 1: Hosting on Railway (PaaS)")
    h1_r.font.name = 'Segoe UI'
    h1_r.font.bold = True
    h1_r.font.color.rgb = navy
    
    p = doc.add_paragraph(
        "Railway (https://railway.app) provides an enterprise containerized Platform-as-a-Service that automatically builds "
        "and runs Django using Nixpacks / Docker, connects to Managed PostgreSQL, provisions SSL certificates, and executes database migrations."
    )
    
    doc.add_heading(level=2).add_run("3.1 Pre-Deployment Repository Manifests").font.color.rgb = navy
    p = doc.add_paragraph("The following files in the repository root control Railway execution:")
    
    p_proc = doc.add_paragraph()
    p_proc.add_run("1. Procfile: ").bold = True
    p_proc.add_run("Specifies the WSGI server command:")
    add_code_block(doc, "web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120")
    
    p_rw = doc.add_paragraph()
    p_rw.add_run("2. railway.json: ").bold = True
    p_rw.add_run("Configures the automated migration, static collection, and startup sequence:")
    add_code_block(doc, """{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 5
  }
}""")
    
    add_callout(doc, 
        "Do NOT include 'python manage.py seed_evaluation_data' in railway.json startCommand on subsequent deploys "
        "if you do not want demo accounts re-created. Only run the seed command manually once from Railway CLI or One-Off execution.",
        title="DATABASE SEEDING BEST PRACTICE",
        border_hex="B91C1C", bg_hex="FEF2F2"
    )
    
    doc.add_heading(level=2).add_run("3.2 Step-by-Step Railway Deployment Workflow").font.color.rgb = navy
    
    steps = [
        ("Step 1: Push Code to Git", 
         "Ensure your latest code with all committed migrations, static assets, and templates is pushed to your GitHub or GitLab repository:\n"
         "git add .\n"
         "git commit -m 'Release v1.0 AMCE VEMS production ready'\n"
         "git push origin main"),
        
        ("Step 2: Create Railway Project & Add PostgreSQL", 
         "1. Log in to https://railway.app.\n"
         "2. Click 'New Project' -> 'Provision PostgreSQL'.\n"
         "3. Railway will spin up a dedicated PostgreSQL database container and expose a private/public connection string variable called DATABASE_URL."),
         
        ("Step 3: Deploy GitHub Repository", 
         "1. In the same project canvas, click '+ New' -> 'GitHub Repo'.\n"
         "2. Select your repository ('AMCE Vendor Evaluation' / 'amce_vems').\n"
         "3. Railway will link the service. Do NOT deploy yet until Environment Variables are defined."),
         
        ("Step 4: Configure Production Environment Variables in Railway", 
         "Navigate to the Web Service -> 'Variables' tab, and add the following keys:\n"
         "• SECRET_KEY = [Generate a 50-character random key using python -c 'import secrets; print(secrets.token_urlsafe(50))']\n"
         "• DEBUG = False\n"
         "• DATABASE_URL = ${{Postgres.DATABASE_URL}} (Railway auto-references the database link)\n"
         "• ALLOWED_HOSTS = .railway.app, vems.amce.ng, 127.0.0.1\n"
         "• CSRF_TRUSTED_ORIGINS = https://*.railway.app, https://vems.amce.ng\n"
         "• SITE_DOMAIN = https://vems.amce.ng (or your Railway generated URL)\n"
         "• EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend\n"
         "• EMAIL_HOST = smtp.office365.com\n"
         "• EMAIL_PORT = 587\n"
         "• EMAIL_USE_TLS = True\n"
         "• EMAIL_HOST_USER = notifications@amce.ng\n"
         "• EMAIL_HOST_PASSWORD = [Your Microsoft 365 App Password]\n"
         "• DEFAULT_FROM_EMAIL = AMCE Evaluation Committee <notifications@amce.ng>\n"
         "• SECURE_SSL_REDIRECT = True"),
         
        ("Step 5: Attach Domain & Deploy", 
         "1. Click 'Settings' -> 'Networking' -> 'Generate Domain' (e.g. amce-vems.up.railway.app) or 'Custom Domain' (vems.amce.ng).\n"
         "2. For custom domain, create a CNAME record in AMCE DNS pointing 'vems' to the Railway domain target.\n"
         "3. Trigger Deploy. Railway will execute Nixpacks build, install Python 3.12+, run collectstatic, apply database migrations, and start Gunicorn."),
         
        ("Step 6: Initialize Clean Superuser on Railway PostgreSQL", 
         "Open Railway CLI or the web terminal on your web container and execute:\n"
         "python manage.py shell -c \"from django.contrib.auth.models import User, Group; from apps.core.models import EvaluatorProfile, Department; from apps.core.management.commands.seed_evaluation_data import Command; Command().handle(); User.objects.exclude(username='admin').delete(); u = User.objects.get(username='admin'); u.set_password('Admin12345!'); u.email='admin@amce.ng'; u.save(); print('Railway Production Superuser Ready!')\"")
    ]
    
    for title, desc in steps:
        h3 = doc.add_heading(level=3)
        h3.add_run(title).font.color.rgb = teal
        p = doc.add_paragraph(desc)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(8)

    # --- OPTION 2: ON-PREMISES MICROSOFT WINDOWS VM ---
    h1 = doc.add_heading(level=1)
    h1_r = h1.add_run("4. Deployment Option 2: Hosting on a Local Microsoft Windows VM")
    h1_r.font.name = 'Segoe UI'
    h1_r.font.bold = True
    h1_r.font.color.rgb = navy
    
    p = doc.add_paragraph(
        "For quaternary healthcare environments requiring full data residency inside the AMCE Abuja intranet "
        "and direct LDAP integration with local Active Directory Domain Controllers (dc01.amce.local), "
        "deploying on a dedicated Windows Server VM (Windows Server 2022 / 2025 Standard) is the authoritative architecture."
    )
    
    doc.add_heading(level=2).add_run("4.1 Server Prerequisites & Architecture").font.color.rgb = navy
    
    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.columns[0].width = Inches(2.2)
    table.columns[1].width = Inches(4.3)
    
    specs = [
        ("Operating System", "Windows Server 2022 Datacenter or Standard (64-bit)"),
        ("Hardware Sizing", "4 vCPUs, 16 GB RAM, 100 GB SSD (C: OS, D: Application & Database)"),
        ("Software Stack", "Python 3.12 (x64), PostgreSQL 16 for Windows, NSSM (Non-Sucking Service Manager), IIS with URL Rewrite & ARR"),
        ("Network & Firewall", "Port 80/443 inbound (HTTP/HTTPS), Port 636 outbound to Domain Controller (LDAPS), Port 587 outbound to SMTP")
    ]
    for i, (k, v) in enumerate(specs):
        row = table.rows[i]
        c0, c1 = row.cells
        set_cell_background(c0, "F1F5F9")
        set_cell_background(c1, "FFFFFF")
        set_cell_margins(c0, 60, 60, 80, 80)
        set_cell_margins(c1, 60, 60, 80, 80)
        c0.text = k
        c0.paragraphs[0].runs[0].font.bold = True
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c1.text = v
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)
        
    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    
    doc.add_heading(level=2).add_run("4.2 Step-by-Step Windows VM Provisioning").font.color.rgb = navy
    
    win_steps = [
        ("Phase A: Install Python 3.12, Git & PostgreSQL 16 on Windows VM",
         "1. Download and run Python 3.12 x64 installer. Check 'Add python.exe to PATH' and install for All Users to C:\\Program Files\\Python312.\n"
         "2. Install Git for Windows from https://git-scm.com.\n"
         "3. Download PostgreSQL 16 Windows x64 Installer from EnterpriseDB:\n"
         "   - Set superuser password: [StrongDbPassword2026!]\n"
         "   - Port: 5432\n"
         "   - Open pgAdmin 4 or SQL Shell (psql) and run:\n"
         "     CREATE DATABASE amce_vems_db;\n"
         "     CREATE USER amce_user WITH PASSWORD 'StrongAppDbPass2026!';\n"
         "     GRANT ALL PRIVILEGES ON DATABASE amce_vems_db TO amce_user;\n"
         "     ALTER DATABASE amce_vems_db OWNER TO amce_user;"),
         
        ("Phase B: Establish Production Directory & Virtual Environment",
         "Open PowerShell as Administrator and run:\n"
         "mkdir C:\\inetpub\\amce_vems\n"
         "cd C:\\inetpub\\amce_vems\n"
         "git clone <YOUR_GIT_REPO_URL> .\n"
         "py -3.12 -m venv venv\n"
         ".\\venv\\Scripts\\Activate.ps1\n"
         "python -m pip install --upgrade pip\n"
         "pip install -r requirements.txt\n"
         "pip install waitress ldap3 psycopg2-binary"),
         
        ("Phase C: Create Secure Production .env File",
         "In C:\\inetpub\\amce_vems\\.env, place the production credentials:"),
    ]
    
    for title, desc in win_steps:
        h3 = doc.add_heading(level=3)
        h3.add_run(title).font.color.rgb = teal
        p = doc.add_paragraph(desc)
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(6)
        
    code_win_env = """# C:\\inetpub\\amce_vems\\.env

# Core Django Security
SECRET_KEY=amce_enterprise_production_secret_key_84920491823091238490
DEBUG=False
ALLOWED_HOSTS=vems.amce.local,vems.amce.ng,127.0.0.1,192.168.10.50
CSRF_TRUSTED_ORIGINS=https://vems.amce.local,https://vems.amce.ng

# Database: Local Windows PostgreSQL 16
DATABASE_URL=postgresql://amce_user:StrongAppDbPass2026!@127.0.0.1:5432/amce_vems_db

# Active Directory Integration (Hospital Domain Controller)
LDAP_SERVER_URI=ldaps://dc01.amce.local:636
LDAP_BIND_DN=CN=svc_vems,OU=ServiceAccounts,DC=amce,DC=local
LDAP_BIND_PASSWORD=ServiceAccountComplexPassword2026!
LDAP_SEARCH_BASE=OU=Staff,DC=amce,DC=local

# Outbound Email Delivery (Microsoft 365 Exchange)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=notifications@amce.ng
EMAIL_HOST_PASSWORD=YourSecureMailAppPassword
DEFAULT_FROM_EMAIL="AMCE Evaluation Committee <notifications@amce.ng>"
SITE_DOMAIN=https://vems.amce.ng
"""
    add_code_block(doc, code_win_env)
    
    doc.add_heading(level=3).add_run("Phase D: Initialize Database, Static Files & Superuser").font.color.rgb = teal
    p = doc.add_paragraph(
        "Run the following in PowerShell within the active virtual environment:\n"
        "python manage.py migrate\n"
        "python manage.py collectstatic --noinput\n"
        "python manage.py seed_evaluation_data\n"
        "# Ensure only the single master admin exists:\n"
        "python manage.py shell -c \"from django.contrib.auth.models import User; User.objects.exclude(username='admin').delete(); u=User.objects.get(username='admin'); u.set_password('Admin12345!'); u.email='admin@amce.ng'; u.save(); print('Clean superuser ready!')\""
    )
    
    doc.add_heading(level=3).add_run("Phase E: Configure Windows Background Service with NSSM").font.color.rgb = teal
    p = doc.add_paragraph(
        "On Windows, standard production WSGI applications are served using `waitress-serve` or Gunicorn under WSL. "
        "`Waitress` is native to pure Windows and runs with production-grade stability. "
        "NSSM (Non-Sucking Service Manager) turns it into an automatic Windows service that boots on server reboot."
    )
    
    nssm_code = """# Download NSSM from https://nssm.cc/download and place nssm.exe in C:\\Windows\\System32

# In PowerShell (Administrator):
nssm install AMCE_VEMS_Service "C:\\inetpub\\amce_vems\\venv\\Scripts\\waitress-serve.exe"
nssm set AMCE_VEMS_Service AppParameters "--listen=127.0.0.1:8000 --threads=8 config.wsgi:application"
nssm set AMCE_VEMS_Service AppDirectory "C:\\inetpub\\amce_vems"
nssm set AMCE_VEMS_Service DisplayName "AMCE Vendor Evaluation Web Service"
nssm set AMCE_VEMS_Service Description "Django WSGI backend for AMCE VEMS"
nssm set AMCE_VEMS_Service Start SERVICE_AUTO_START
nssm set AMCE_VEMS_Service AppStdout "C:\\inetpub\\amce_vems\\logs\\service.log"
nssm set AMCE_VEMS_Service AppStderr "C:\\inetpub\\amce_vems\\logs\\error.log"

# Start the Service:
nssm start AMCE_VEMS_Service"""
    add_code_block(doc, nssm_code)
    
    doc.add_heading(level=3).add_run("Phase F: Configure Microsoft IIS as Reverse Proxy & SSL Gateway").font.color.rgb = teal
    p = doc.add_paragraph(
        "Internet Information Services (IIS) provides the frontend HTTPS endpoint, terminates SSL (using an AMCE Enterprise Internal CA certificate or Let's Encrypt), and reverse-proxies requests to Waitress at 127.0.0.1:8000.\n\n"
        "1. Open Server Manager -> Add Roles and Features -> Install 'Web Server (IIS)'.\n"
        "2. Install two essential IIS official extensions:\n"
        "   • Application Request Routing (ARR) 3.0\n"
        "   • URL Rewrite 2.1\n"
        "3. In IIS Manager, click Server Node -> 'Application Request Routing Cache' -> 'Server Proxy Settings' -> Check 'Enable proxy' -> Apply.\n"
        "4. Place this web.config file in `C:\\inetpub\\amce_vems\\web.config`:"
    )
    
    web_config = """<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <!-- Direct Static Files to Disk for Max Speed -->
                <rule name="StaticFiles" stopProcessing="true">
                    <match url="^static/(.*)$" />
                    <action type="Rewrite" url="staticfiles/{R:1}" />
                </rule>
                <!-- Reverse Proxy all dynamic traffic to Django Waitress -->
                <rule name="ReverseProxyToWaitress" stopProcessing="true">
                    <match url="(.*)" />
                    <action type="Rewrite" url="http://127.0.0.1:8000/{R:1}" />
                    <serverVariables>
                        <set name="HTTP_X_FORWARDED_PROTO" value="https" />
                        <set name="HTTP_X_FORWARDED_HOST" value="{HTTP_HOST}" />
                    </serverVariables>
                </rule>
            </rules>
        </rewrite>
        <httpProtocol>
            <customHeaders>
                <add name="X-Frame-Options" value="DENY" />
                <add name="X-Content-Type-Options" value="nosniff" />
            </customHeaders>
        </httpProtocol>
    </system.webServer>
</configuration>"""
    add_code_block(doc, web_config)
    
    doc.add_heading(level=3).add_run("Phase G: Bind SSL Certificate in IIS").font.color.rgb = teal
    p = doc.add_paragraph(
        "1. Open IIS Manager -> Sites -> Add Website.\n"
        "2. Site name: `AMCE_VEMS`.\n"
        "3. Physical path: `C:\\inetpub\\amce_vems`.\n"
        "4. Binding: Type `https`, Port `443`, Host name `vems.amce.ng` (or `vems.amce.local`).\n"
        "5. Select your AMCE Hospital Wildcard / Domain SSL certificate.\n"
        "6. Test from any hospital workstation: `https://vems.amce.ng/login/`."
    )
    
    # --- COMPARISON & DECISION MATRIX ---
    h1 = doc.add_heading(level=1)
    h1_r = h1.add_run("5. Architecture Comparison & Decision Matrix")
    h1_r.font.name = 'Segoe UI'
    h1_r.font.bold = True
    h1_r.font.color.rgb = navy
    
    comp_table = doc.add_table(rows=7, cols=3)
    comp_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    comp_table.columns[0].width = Inches(2.0)
    comp_table.columns[1].width = Inches(2.25)
    comp_table.columns[2].width = Inches(2.25)
    
    matrix = [
        ("Criterion", "Option 1: Railway (PaaS)", "Option 2: Windows Server VM (On-Prem)"),
        ("Deployment Speed", "15 - 30 minutes (Fully automated)", "1 - 2 hours (OS & IIS setup)"),
        ("Maintenance Burden", "Zero OS patching; automated updates", "Requires Windows updates & DB backups"),
        ("Active Directory Sync", "Azure AD / Entra ID via Graph API", "Native On-Premises Windows Server AD (LDAPS)"),
        ("Data Sovereignty", "Hosted on Cloud (Railway / AWS US/EU)", "100% On-Premises inside AMCE Datacenter"),
        ("Scalability", "Instant vertical/horizontal slider", "Scale VM CPU/RAM via Hyper-V/VMware"),
        ("Backup & Recovery", "Automated Railway DB snapshots", "Veeam / Windows Server Backup / pg_dump")
    ]
    
    for i, row in enumerate(comp_table.rows):
        k, v1, v2 = matrix[i]
        c0, c1, c2 = row.cells
        set_cell_margins(c0, 60, 60, 80, 80)
        set_cell_margins(c1, 60, 60, 80, 80)
        set_cell_margins(c2, 60, 60, 80, 80)
        if i == 0:
            set_cell_background(c0, "0B2545")
            set_cell_background(c1, "0B2545")
            set_cell_background(c2, "0B2545")
            for c, text in [(c0, k), (c1, v1), (c2, v2)]:
                c.text = text
                c.paragraphs[0].runs[0].font.bold = True
                c.paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
        else:
            set_cell_background(c0, "F8FAFC")
            set_cell_background(c1, "FFFFFF")
            set_cell_background(c2, "FFFFFF")
            c0.text = k
            c0.paragraphs[0].runs[0].font.bold = True
            c1.text = v1
            c2.text = v2
            for c in (c0, c1, c2):
                c.paragraphs[0].runs[0].font.size = Pt(9)
                
    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    
    # --- CHECKLIST & VERIFICATION ---
    h1 = doc.add_heading(level=1)
    h1_r = h1.add_run("6. Production Readiness Go-Live Checklist")
    h1_r.font.name = 'Segoe UI'
    h1_r.font.bold = True
    h1_r.font.color.rgb = navy
    
    chk_items = [
        ("Security Audit", "DEBUG is set to False in environment. Random SECRET_KEY is set. SECURE_SSL_REDIRECT is enabled."),
        ("Host Validation", "ALLOWED_HOSTS and CSRF_TRUSTED_ORIGINS contain exact FQDNs (vems.amce.ng)."),
        ("Database Connection", "PostgreSQL 16 connection is verified with connection pooling (CONN_MAX_AGE=600)."),
        ("Static Assets", "python manage.py collectstatic compiled all CSS, JS, and logos into staticfiles directory."),
        ("Master Admin Access", "Primary superuser 'admin' is verified with password 'Admin12345!' and official email 'admin@amce.ng'."),
        ("Email Gateway Subsystem", "Live verification email dispatched from /management/messages/setup/ to an AMCE inbox with green 'Operational' status."),
        ("Active Directory Verification", "Tested /management/users/from-ad/ lookup against hospital domain controller."),
        ("Database Backup Automation", "Configured daily automated pg_dump backup script with 30-day retention.")
    ]
    
    for title, desc in chk_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        r_box = p.add_run("[  ] ")
        r_box.font.name = 'Consolas'
        r_box.font.bold = True
        r_box.font.color.rgb = teal
        
        r_t = p.add_run(f"{title}: ")
        r_t.font.name = 'Segoe UI'
        r_t.font.bold = True
        r_t.font.color.rgb = navy
        
        r_d = p.add_run(desc)
        r_d.font.name = 'Segoe UI'
        r_d.font.size = Pt(9.5)
        r_d.font.color.rgb = dark

    # Save Document
    doc.save(output_path)
    print(f"Document successfully created at: {output_path}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'AMCE_VEMS_Production_Deployment_Guide.docx'
    create_document(target)
