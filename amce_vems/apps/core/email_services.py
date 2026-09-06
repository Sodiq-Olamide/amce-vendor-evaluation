import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from apps.core.models import EmailMessageTemplate, EmailNotificationLog

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """
    Centralized service for dispatching dynamic notification emails using database-backed
    EmailMessageTemplate records.
    Automatically replaces dynamic tags like:
    {{first_name}}, {{last_name}}, {{email}}, {{username}}, {{password_note}},
    {{role}}, {{department}}, {{designation}}, {{login_url}}, {{portal_name}}
    """

    DEFAULT_TEMPLATES = {
        'USER_WELCOME': {
            'title': 'New User Provisioned / Welcome Email',
            'subject': 'Welcome to the AMCE EHR Vendor Evaluation Portal - Account Provisioned',
            'from_name': 'AMCE Evaluation Committee',
            'from_email': 'noreply@amce.org',
            'body_html': """
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 620px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
    <div style="background-color: #0B2545; padding: 24px; text-align: center; color: #ffffff;">
        <h2 style="margin: 0; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">AFRICAN MEDICAL CENTRE OF EXCELLENCE</h2>
        <p style="margin: 6px 0 0; color: #139A8C; font-size: 14px; text-transform: uppercase; font-weight: 600;">EHR Vendor Demonstration Evaluation Portal</p>
    </div>
    <div style="padding: 30px 25px; color: #1e293b; line-height: 1.6;">
        <p style="font-size: 16px; margin-top: 0;">Dear <strong>{{first_name}} {{last_name}}</strong>,</p>
        <p>An official user account has been provisioned for you on the <strong>AMCE Vendor Evaluation Management System (VEMS)</strong>.</p>
        
        <div style="background-color: #f8fafc; border-left: 4px solid #139A8C; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0 0 8px;"><strong>Account Profile Details:</strong></p>
            <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
                <tr><td style="padding: 4px 0; width: 140px; color: #64748b;">Official Email:</td><td style="font-weight: 600;">{{email}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Login Username:</td><td style="font-weight: 600;">{{username}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Assigned Role:</td><td style="font-weight: 600; color: #0B2545;">{{role}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Department:</td><td>{{department}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Designation:</td><td>{{designation}}</td></tr>
            </table>
        </div>

        <p>{{password_note}}</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{login_url}}" style="background-color: #0B2545; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Access Evaluation Portal &rarr;</a>
        </div>

        <p style="font-size: 13px; color: #64748b; margin-bottom: 0;">If you have any questions or require support during demonstration sessions, please contact the AMCE IT & Clinical Informatics steering committee.</p>
    </div>
    <div style="background-color: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
        African Medical Centre of Excellence (AMCE) Abuja &bull; Confidential Evaluation System
    </div>
</div>
""",
            'body_text': """Welcome to AMCE Vendor Evaluation Management System

Dear {{first_name}} {{last_name}},

An account has been created for you on the AMCE EHR Vendor Evaluation Portal.

Account Details:
- Official Email: {{email}}
- Username: {{username}}
- Role: {{role}}
- Department: {{department}}
- Designation: {{designation}}

{{password_note}}

Portal Access URL: {{login_url}}

Best regards,
AMCE Evaluation Committee
"""
        },
        'AD_USER_WELCOME': {
            'title': 'Active Directory User Linked Email',
            'subject': 'AMCE EHR Vendor Evaluation - Active Directory Account Synchronized',
            'from_name': 'AMCE Evaluation Committee',
            'from_email': 'noreply@amce.org',
            'body_html': """
<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 620px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
    <div style="background-color: #0B2545; padding: 24px; text-align: center; color: #ffffff;">
        <h2 style="margin: 0; font-size: 22px; font-weight: 700;">AFRICAN MEDICAL CENTRE OF EXCELLENCE</h2>
        <p style="margin: 6px 0 0; color: #139A8C; font-size: 14px; text-transform: uppercase; font-weight: 600;">Active Directory Single Sign-On Enabled</p>
    </div>
    <div style="padding: 30px 25px; color: #1e293b; line-height: 1.6;">
        <p style="font-size: 16px; margin-top: 0;">Hello <strong>{{first_name}} {{last_name}}</strong>,</p>
        <p>Your hospital Active Directory credentials have been successfully linked to the <strong>AMCE EHR Vendor Evaluation Portal</strong>.</p>
        
        <div style="background-color: #f8fafc; border-left: 4px solid #0284c7; padding: 16px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0 0 8px;"><strong>Evaluation Assignment Profile:</strong></p>
            <table style="width: 100%; font-size: 14px; border-collapse: collapse;">
                <tr><td style="padding: 4px 0; width: 140px; color: #64748b;">Account Email:</td><td style="font-weight: 600;">{{email}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Evaluator Role:</td><td style="font-weight: 600; color: #0B2545;">{{role}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Department:</td><td>{{department}}</td></tr>
                <tr><td style="padding: 4px 0; color: #64748b;">Official Title:</td><td>{{designation}}</td></tr>
            </table>
        </div>

        <p>You can sign in directly using your regular organization hospital credentials (SSO / Active Directory password).</p>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{login_url}}" style="background-color: #0B2545; color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block;">Open Evaluation Portal &rarr;</a>
        </div>
    </div>
    <div style="background-color: #f1f5f9; padding: 15px; text-align: center; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
        African Medical Centre of Excellence (AMCE) Abuja &bull; Confidential Evaluation System
    </div>
</div>
""",
            'body_text': """AMCE EHR Vendor Evaluation - Active Directory Account Synchronized

Hello {{first_name}} {{last_name}},

Your Active Directory account ({{email}}) is now linked to the AMCE Vendor Evaluation Portal with role: {{role}}.
You can log in directly using your hospital credentials at: {{login_url}}

Best regards,
AMCE Evaluation Committee
"""
        }
    }

    @classmethod
    def get_or_create_template(cls, event_type):
        """Retrieves template from database or initializes with default content."""
        tpl = EmailMessageTemplate.objects.filter(event_type=event_type).first()
        if not tpl and event_type in cls.DEFAULT_TEMPLATES:
            data = cls.DEFAULT_TEMPLATES[event_type]
            tpl = EmailMessageTemplate.objects.create(
                event_type=event_type,
                title=data['title'],
                subject=data['subject'],
                from_name=data['from_name'],
                from_email=data['from_email'],
                body_html=data['body_html'],
                body_text=data['body_text'],
                is_active=True
            )
        return tpl

    @classmethod
    def send_user_welcome_email(cls, user, password=None, is_ad_provisioned=False):
        """
        Triggers automatic welcome notification email upon user creation.
        """
        if not user.email:
            logger.warning(f"Cannot send welcome email: user {user.username} has no email address.")
            return False

        event_type = 'AD_USER_WELCOME' if is_ad_provisioned else 'USER_WELCOME'
        tpl = cls.get_or_create_template(event_type)

        if not tpl or not tpl.is_active:
            logger.info(f"Email template for {event_type} is inactive or not found. Skipping email.")
            return False

        # Build context placeholders
        domain = getattr(settings, 'SITE_DOMAIN', 'http://127.0.0.1:8089').rstrip('/')
        login_url = f"{domain}/login/"
        
        profile = getattr(user, 'evaluator_profile', None)
        dept_name = profile.department.name if profile and profile.department else "General Hospital"
        designation = profile.designation if profile else "Evaluator"
        
        group_name = user.groups.first().name if user.groups.exists() else ("Administrator" if user.is_superuser else "Evaluator")

        if password:
            pw_note = f"<strong>Initial Security Password:</strong> <code style='background: #e2e8f0; padding: 2px 6px; border-radius: 4px;'>{password}</code><br><span style='color: #64748b; font-size: 12px;'>Please change your password upon initial login if required.</span>"
        elif is_ad_provisioned:
            pw_note = "<strong>Authentication Method:</strong> Sign in with your official AMCE Active Directory credentials (Single Sign-On)."
        else:
            pw_note = "Your account has been configured with password authentication by the system administrator."

        context = {
            'first_name': user.first_name or user.username,
            'last_name': user.last_name or '',
            'email': user.email,
            'username': user.username,
            'role': group_name,
            'department': dept_name,
            'designation': designation,
            'login_url': login_url,
            'password_note': pw_note,
            'portal_name': 'AMCE Vendor Evaluation Portal',
        }

        # Render subject and bodies
        subject = tpl.subject
        body_html = tpl.body_html
        body_text = tpl.body_text or ""

        for key, val in context.items():
            tag = f"{{{{{key}}}}}"
            subject = subject.replace(tag, str(val))
            body_html = body_html.replace(tag, str(val))
            body_text = body_text.replace(tag, str(val))

        from_header = f"{tpl.from_name} <{tpl.from_email}>" if tpl.from_name else tpl.from_email

        # Determine delivery status based on backend and execution
        is_console = 'console' in settings.EMAIL_BACKEND.lower() or 'dummy' in settings.EMAIL_BACKEND.lower()
        status = 'SIMULATED' if is_console else 'SENT'
        error_msg = None
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=body_text,
                from_email=from_header,
                to=[user.email]
            )
            msg.attach_alternative(body_html, "text/html")
            msg.send(fail_silently=False)
            if is_console:
                logger.info(f"Welcome email simulated/printed to console for {user.email} (ConsoleBackend active)")
            else:
                logger.info(f"Welcome email successfully sent via SMTP to {user.email}")
        except Exception as e:
            status = 'FAILED'
            error_msg = str(e)
            logger.error(f"Failed to send welcome email to {user.email}: {e}")

        # Log to EmailNotificationLog
        EmailNotificationLog.objects.create(
            recipient_user=user,
            recipient_email=user.email,
            subject=subject,
            body_snapshot=body_html,
            event_type=event_type,
            status=status,
            error_message=error_msg
        )

        return status in ('SENT', 'SIMULATED')
