import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class ActiveDirectoryService:
    """
    Active Directory integration service for AMCE VEMS.
    Supports querying organization Active Directory via Microsoft Graph API (Azure AD / Entra ID)
    or on-premises LDAP / LDAPS.
    Includes robust fallback mock directory for immediate demo & testing.
    """

    DEMO_DIRECTORY = [
        {
            "email": "a.bello@amce.org",
            "username": "a.bello@amce.org",
            "first_name": "Amina",
            "last_name": "Bello",
            "designation": "Nurse Manager - ICU & Inpatient",
            "department": "Nursing Services",
            "employee_id": "AMCE-EMP-1021",
            "phone": "+234 803 111 2233"
        },
        {
            "email": "c.okonkwo@amce.org",
            "username": "c.okonkwo@amce.org",
            "first_name": "Chidi",
            "last_name": "Okonkwo",
            "designation": "Chief Information Officer / IT Lead",
            "department": "Information Technology (IT & Clinical Informatics)",
            "employee_id": "AMCE-EMP-0012",
            "phone": "+234 802 333 4455"
        },
        {
            "email": "e.adeyemi@amce.org",
            "username": "e.adeyemi@amce.org",
            "first_name": "Emeka",
            "last_name": "Adeyemi",
            "designation": "Consultant Medical Oncologist",
            "department": "Oncology Services",
            "employee_id": "AMCE-EMP-2045",
            "phone": "+234 805 555 6677"
        },
        {
            "email": "f.ibrahim@amce.org",
            "username": "f.ibrahim@amce.org",
            "first_name": "Fatima",
            "last_name": "Ibrahim",
            "designation": "Head of Cardiovascular Nursing & Cath Lab",
            "department": "Cardiovascular Services",
            "employee_id": "AMCE-EMP-3011",
            "phone": "+234 809 777 8899"
        },
        {
            "email": "k.mensah@amce.org",
            "username": "k.mensah@amce.org",
            "first_name": "Kwame",
            "last_name": "Mensah",
            "designation": "Chief Medical Officer",
            "department": "Executive & Clinical Administration",
            "employee_id": "AMCE-EMP-0005",
            "phone": "+234 814 222 3344"
        },
        {
            "email": "o.balogun@amce.org",
            "username": "o.balogun@amce.org",
            "first_name": "Olumide",
            "last_name": "Balogun",
            "designation": "Chief Radiographer & Imaging Systems Lead",
            "department": "Radiology and Nuclear Medicine",
            "employee_id": "AMCE-EMP-4018",
            "phone": "+234 818 444 5566"
        },
        {
            "email": "n.danladi@amce.org",
            "username": "n.danladi@amce.org",
            "first_name": "Nafisat",
            "last_name": "Danladi",
            "designation": "Director of Finance & Revenue Cycle (ERP)",
            "department": "Finance, ERP & Hospital Procurement",
            "employee_id": "AMCE-EMP-0018",
            "phone": "+234 803 888 9900"
        },
        {
            "email": "t.okafor@amce.org",
            "username": "t.okafor@amce.org",
            "first_name": "Tochukwu",
            "last_name": "Okafor",
            "designation": "Laboratory Scientist - Blood Bank & Transfusion",
            "department": "Laboratory Services & Blood Bank",
            "employee_id": "AMCE-EMP-5022",
            "phone": "+234 807 123 4567"
        }
    ]

    @classmethod
    def is_azure_ad_configured(cls):
        """Checks if real Azure AD / Microsoft Graph credentials are set in environment."""
        tenant_id = os.environ.get('AZURE_AD_TENANT_ID')
        client_id = os.environ.get('AZURE_AD_CLIENT_ID')
        client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET')
        return bool(tenant_id and client_id and client_secret)

    @classmethod
    def get_azure_ad_access_token(cls):
        """Fetches application token from Microsoft identity platform."""
        import requests
        tenant_id = os.environ.get('AZURE_AD_TENANT_ID')
        client_id = os.environ.get('AZURE_AD_CLIENT_ID')
        client_secret = os.environ.get('AZURE_AD_CLIENT_SECRET')

        url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default',
            'grant_type': 'client_credentials'
        }
        resp = requests.post(url, data=data, timeout=5)
        if resp.status_code == 200:
            return resp.json().get('access_token')
        logger.error(f"Failed to fetch Azure AD token: {resp.text}")
        return None

    @classmethod
    def search_users(cls, query=""):
        """
        Search for staff members by email, name, or designation.
        Returns a list of matching user dictionaries.
        """
        q = (query or "").strip().lower()

        # If Azure AD credentials exist, query live Microsoft Graph API
        if cls.is_azure_ad_configured():
            try:
                import requests
                token = cls.get_azure_ad_access_token()
                if token:
                    headers = {
                        'Authorization': f'Bearer {token}',
                        'ConsistencyLevel': 'eventual'
                    }
                    if q:
                        graph_url = f"https://graph.microsoft.com/v1.0/users?$filter=startswith(mail, '{q}') or startswith(displayName, '{q}')&$select=id,displayName,givenName,surname,mail,userPrincipalName,jobTitle,department,employeeId,mobilePhone&$top=25"
                    else:
                        graph_url = "https://graph.microsoft.com/v1.0/users?$select=id,displayName,givenName,surname,mail,userPrincipalName,jobTitle,department,employeeId,mobilePhone&$top=25"

                    res = requests.get(graph_url, headers=headers, timeout=6)
                    if res.status_code == 200:
                        results = []
                        for u in res.json().get('value', []):
                            email = (u.get('mail') or u.get('userPrincipalName') or "").lower()
                            if not email:
                                continue
                            results.append({
                                "email": email,
                                "username": email,
                                "first_name": u.get('givenName') or "",
                                "last_name": u.get('surname') or "",
                                "designation": u.get('jobTitle') or "Staff Member",
                                "department": u.get('department') or "General Hospital",
                                "employee_id": u.get('employeeId') or f"AMCE-AD-{u.get('id')[:6]}",
                                "phone": u.get('mobilePhone') or ""
                            })
                        return results
            except Exception as e:
                logger.exception(f"Error querying Microsoft Graph AD: {e}")

        # Fallback to local organization directory
        if not q:
            return cls.DEMO_DIRECTORY

        matches = []
        for staff in cls.DEMO_DIRECTORY:
            if (q in staff['email'].lower() or 
                q in staff['first_name'].lower() or 
                q in staff['last_name'].lower() or 
                q in staff['designation'].lower() or
                q in staff['department'].lower()):
                matches.append(staff)
        return matches

    @classmethod
    def get_user_by_email(cls, email):
        """Exact lookup of a user by email/UPN in the AD."""
        email_clean = (email or "").strip().lower()
        users = cls.search_users(email_clean)
        for u in users:
            if u['email'].lower() == email_clean:
                return u
        return None
