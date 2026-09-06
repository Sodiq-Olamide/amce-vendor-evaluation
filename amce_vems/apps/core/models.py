from django.db import models
from django.contrib.auth.models import User

class Department(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    division = models.CharField(max_length=100, default='Clinical')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class EvaluatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='evaluator_profile')
    employee_id = models.CharField(max_length=50, unique=True, blank=True, null=True)
    designation = models.CharField(max_length=255)
    department = models.ForeignKey(Department, on_delete=models.RESTRICT, related_name='evaluators')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.designation} - {self.department.name})"


class EmailMessageTemplate(models.Model):
    """
    Dynamic message template for system events such as User Creation / Welcome,
    Password Resets, Demonstration Reminders, and Scorecard Submission Confirmations.
    Supports variables like {{first_name}}, {{last_name}}, {{email}}, {{username}},
    {{role}}, {{department}}, {{designation}}, {{login_url}}, {{portal_name}}.
    """
    EVENT_CHOICES = [
        ('USER_WELCOME', 'New User Provisioned / Welcome Email'),
        ('AD_USER_WELCOME', 'Active Directory User Linked Email'),
        ('SCORECARD_SUBMITTED', 'Scorecard Submission Receipt'),
        ('SUBMISSION_LOCKED', 'Scorecard Integrity Lock Confirmation'),
    ]

    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES, unique=True)
    title = models.CharField(max_length=255, help_text="Friendly label for this email template")
    subject = models.CharField(max_length=255, help_text="Email subject line with dynamic tags like {{first_name}}")
    body_html = models.TextField(help_text="HTML formatted email body with dynamic variable placeholders")
    body_text = models.TextField(blank=True, null=True, help_text="Plain text fallback version")
    is_active = models.BooleanField(default=True, help_text="Toggle automatic sending on/off for this event")
    from_name = models.CharField(max_length=150, default="AMCE Vendor Evaluation Portal", help_text="Sender display name")
    from_email = models.EmailField(default="noreply@amce.org", help_text="Sender email address")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_event_type_display()} ({'Active' if self.is_active else 'Disabled'})"


class EmailNotificationLog(models.Model):
    """
    Audit log of all automatic emails triggered and sent by the portal.
    """
    STATUS_CHOICES = [
        ('SENT', 'Sent Successfully'),
        ('FAILED', 'Failed'),
        ('SIMULATED', 'Simulated / Development Console'),
    ]

    recipient_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_emails')
    recipient_email = models.EmailField()
    subject = models.CharField(max_length=255)
    body_snapshot = models.TextField()
    event_type = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SENT')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"[{self.status}] {self.recipient_email} - {self.subject} ({self.sent_at:%Y-%m-%d %H:%M})"

