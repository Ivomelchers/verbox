# Admin Dashboard & Email Testing — Design Spec

**Date:** 2026-06-11  
**Phase:** 9 (MVP Testing)  
**Audience:** Developer + non-technical founder  
**Purpose:** Enable testing of email functionality and user management without Resend dashboard access

---

## Problem Statement

Currently:
- Email functionality implemented but untested
- No way to resend verification/password reset emails to test users
- No visibility into which emails are being sent to whom
- Founder cannot perform admin operations without technical knowledge
- Need to log into Resend dashboard to verify emails are sending

**Goals:**
1. Test email functionality during MVP phase
2. Provide founder-friendly interface for common admin tasks
3. Maintain email audit trail for testing and debugging
4. Keep all tooling within Django admin (minimize new infrastructure)

---

## Solution Overview

Enhance Django admin with:
1. **EmailLog model** — persistent record of all sent emails
2. **Custom admin dashboard** — home view with stats, recent emails, quick actions
3. **Admin bulk actions** — one-click operations on User objects
4. **Resend integration** — link to Resend for delivery status, optional background sync

---

## Detailed Design

### 1. EmailLog Model

**Location:** `backend/apps/accounts/models.py`

```python
class EmailLog(models.Model):
    """Audit trail of all transactional emails sent via Resend."""
    
    class EmailType(models.TextChoices):
        VERIFICATION = "verification", "Email Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"
        TEST = "test", "Test Email"
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        DELIVERED = "delivered", "Delivered"
        BOUNCED = "bounced", "Bounced"
        FAILED = "failed", "Failed"
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_logs")
    recipient_email = models.EmailField()
    email_type = models.CharField(max_length=20, choices=EmailType.choices)
    subject = models.CharField(max_length=255)
    
    sent_at = models.DateTimeField(auto_now_add=True)
    resend_message_id = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        help_text="Message ID returned from Resend API"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Delivery status (pending until checked from Resend)"
    )
    status_checked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["user", "-sent_at"]),
            models.Index(fields=["status"]),
        ]
    
    def __str__(self):
        return f"{self.email_type} → {self.recipient_email} ({self.status})"
```

**Why:**
- Audit trail for testing and debugging
- Links to User for quick filtering
- `resend_message_id` allows querying Resend API for delivery confirmation
- `status` field shows at-a-glance whether email was delivered
- Indexed on user + date for fast dashboard queries

---

### 2. EmailLog Admin

**Location:** `backend/apps/accounts/admin.py` (extend)

```python
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("sent_at", "user", "recipient_email", "email_type", "status")
    list_filter = ("email_type", "status", "sent_at")
    search_fields = ("user__email", "recipient_email")
    readonly_fields = ("sent_at", "resend_message_id", "status_checked_at")
    ordering = ["-sent_at"]
```

Allows viewing email history and filtering by type/status in standard admin.

---

### 3. Email Sending Service

**Location:** `backend/apps/accounts/services.py` (new file)

Core function that all email operations use:

```python
def send_email(user: User, email_type: str, subject: str, recipient: str, template_data: dict):
    """
    Send email via Resend and log to database.
    
    Args:
        user: User object
        email_type: EmailLog.EmailType choice
        subject: Email subject line
        recipient: Recipient email address
        template_data: Dict for template rendering
    
    Returns:
        EmailLog object with resend_message_id
    """
    # Render template (verification link, reset token, etc.)
    html_body = render_template(f"emails/{email_type}.html", template_data)
    
    # Send via Resend
    response = resend.Emails.send(
        from_="noreply@vermogenspeil.nl",
        to=recipient,
        subject=subject,
        html=html_body,
    )
    
    # Log to database
    email_log = EmailLog.objects.create(
        user=user,
        recipient_email=recipient,
        email_type=email_type,
        subject=subject,
        resend_message_id=response.get("id"),  # Resend returns message ID
        status=EmailLog.Status.PENDING,
    )
    
    return email_log
```

**Usage examples:**
```python
# In registration flow:
send_email(user, "verification", subject="Verify your email", recipient=user.email, template_data={...})

# In password reset:
send_email(user, "password_reset", subject="Reset your password", recipient=user.email, template_data={...})
```

Benefits:
- Single source of truth for email sending
- Automatic logging
- Easy to add new email types
- Testable in isolation

---

### 4. Admin Bulk Actions

**Location:** Extend `UserAdmin` in `backend/apps/accounts/admin.py`

```python
def resend_verification_email(modeladmin, request, queryset):
    """Send verification email to selected users."""
    count = 0
    for user in queryset:
        if not user.email_verified:
            # Generate token and send email
            token = EmailVerificationToken.objects.create(user=user)
            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
            send_email(
                user=user,
                email_type="verification",
                subject="Verify your email — Vermogenspeil",
                recipient=user.email,
                template_data={"verification_link": verification_link},
            )
            count += 1
    
    modeladmin.message_user(
        request, 
        f"Sent {count} verification emails", 
        messages.SUCCESS
    )

resend_verification_email.short_description = "Resend verification email"


def send_password_reset_email(modeladmin, request, queryset):
    """Send password reset link to selected users."""
    count = 0
    for user in queryset:
        token = PasswordResetToken.objects.create(user=user)
        reset_link = f"{settings.FRONTEND_URL}/auth/password/reset?token={token.token}"
        send_email(
            user=user,
            email_type="password_reset",
            subject="Reset your password — Vermogenspeil",
            recipient=user.email,
            template_data={"reset_link": reset_link},
        )
        count += 1
    
    modeladmin.message_user(
        request,
        f"Sent {count} password reset emails",
        messages.SUCCESS
    )

send_password_reset_email.short_description = "Send password reset link"


class UserAdmin(DjangoUserAdmin):
    # ... existing code ...
    
    actions = [resend_verification_email, send_password_reset_email]
```

**Founder experience:**
1. Open `/admin/accounts/user/`
2. Checkboxes next to users
3. Select users
4. Dropdown "Action" → "Resend verification email"
5. Click Go
6. Green message: "Sent 3 verification emails"

---

### 5. Custom Admin Dashboard

**Location:** `backend/config/admin.py` (new file)

Create custom admin site with home view:

```python
from django.contrib.admin import AdminSite
from django.shortcuts import render
from apps.accounts.models import User, EmailLog

class CustomAdminSite(AdminSite):
    site_header = "Vermogenspeil — Admin"
    site_title = "Vermogenspeil Admin"
    
    def index(self, request, extra_context=None):
        """Custom dashboard home view."""
        
        # Stats
        total_users = User.objects.count()
        unverified_users = User.objects.filter(email_verified=False).count()
        recent_users = User.objects.order_by("-date_joined")[:5]
        recent_emails = EmailLog.objects.select_related("user").order_by("-sent_at")[:10]
        
        pending_emails = EmailLog.objects.filter(status="pending").count()
        
        context = extra_context or {}
        context.update({
            "total_users": total_users,
            "unverified_users": unverified_users,
            "recent_users": recent_users,
            "recent_emails": recent_emails,
            "pending_emails": pending_emails,
            "title": "Dashboard",
        })
        
        return render(request, "admin/custom_index.html", context)

admin_site = CustomAdminSite(name="vermogenspeil_admin")
```

**Template:** `backend/templates/admin/custom_index.html`

```html
{% extends "admin/index.html" %}

{% block content %}
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
  <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
    <h3>👥 Users</h3>
    <p><strong>{{ total_users }}</strong> total users</p>
    <p><strong style="color: orange;">{{ unverified_users }}</strong> unverified</p>
  </div>
  
  <div style="border: 1px solid #ddd; padding: 15px; border-radius: 5px;">
    <h3>📧 Emails</h3>
    <p><strong>{{ pending_emails }}</strong> pending delivery</p>
  </div>
</div>

<div style="margin-bottom: 30px;">
  <h3>Recent Users (Last 5)</h3>
  <table style="width: 100%; border-collapse: collapse;">
    <thead>
      <tr style="background: #f5f5f5;">
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Email</th>
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Name</th>
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Joined</th>
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Verified</th>
      </tr>
    </thead>
    <tbody>
      {% for user in recent_users %}
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px;">{{ user.email }}</td>
        <td style="padding: 8px;">{{ user.first_name }} {{ user.last_name }}</td>
        <td style="padding: 8px;">{{ user.date_joined|date:"Y-m-d H:i" }}</td>
        <td style="padding: 8px;">
          {% if user.email_verified %}✅{% else %}❌{% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

<div>
  <h3>Recent Emails Sent (Last 10)</h3>
  <table style="width: 100%; border-collapse: collapse;">
    <thead>
      <tr style="background: #f5f5f5;">
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Sent</th>
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">To</th>
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Type</th>
        <th style="padding: 8px; text-align: left; border-bottom: 1px solid #ddd;">Status</th>
      </tr>
    </thead>
    <tbody>
      {% for email in recent_emails %}
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 8px; font-size: 12px;">{{ email.sent_at|date:"Y-m-d H:i:s" }}</td>
        <td style="padding: 8px;">{{ email.recipient_email }}</td>
        <td style="padding: 8px;">{{ email.get_email_type_display }}</td>
        <td style="padding: 8px;">
          {% if email.status == "delivered" %}✅{% elif email.status == "pending" %}⏳{% else %}❌{% endif %}
          {{ email.get_status_display }}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{{ block.super }}
{% endblock %}
```

Register in `config/urls.py`:
```python
from config.admin import admin_site

urlpatterns = [
    path("admin/", admin_site.urls),
    # ... rest
]
```

---

### 6. Resend Status Sync (Optional)

**Location:** `backend/apps/accounts/tasks.py` (Celery task)

Periodically fetch delivery status from Resend API:

```python
@shared_task
def sync_email_delivery_status():
    """Check pending emails with Resend every 5 minutes."""
    pending = EmailLog.objects.filter(status="pending")
    
    for email_log in pending:
        if not email_log.resend_message_id:
            continue
        
        # Query Resend API
        response = resend.Emails.get(email_log.resend_message_id)
        status = response.get("status")  # "delivered", "bounced", "failed"
        
        if status:
            email_log.status = status
            email_log.status_checked_at = timezone.now()
            email_log.save()
```

Register in `config/celery.py`:
```python
app.conf.beat_schedule = {
    "sync-email-delivery": {
        "task": "apps.accounts.tasks.sync_email_delivery_status",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}
```

**Note:** Optional because Resend's test mode doesn't track status. Can be added later if needed.

---

## Database Schema

**Migration:** Create `EmailLog` model with:
- FK to User
- recipient_email, email_type, subject (for display)
- sent_at (auto_now_add)
- resend_message_id (nullable)
- status + status_checked_at

Indexes on (user, -sent_at) and (status).

---

## Testing Strategy (During MVP)

1. **Email sending:** Use Resend test mode or real mode with test email address
2. **Dashboard:** Founder can see emails appear in real-time
3. **Verification:** Open admin → Recent Emails → check recipient, type, status
4. **Resend integration:** Verify `resend_message_id` is populated (proves API call worked)

---

## Implementation Priority

**Phase 1 (MVP testing):**
1. EmailLog model + admin
2. send_email() service + all code paths use it
3. Admin dashboard (basic stats + recent emails)
4. Bulk actions (resend verification, password reset)

**Phase 2 (if needed during testing):**
5. Resend status sync task

---

## Success Criteria

- ✅ Founder can resend verification emails from admin without CLI
- ✅ Founder can trigger password reset links
- ✅ Recent emails visible on admin dashboard (last 10)
- ✅ Email type, recipient, status visible at a glance
- ✅ No 3rd-party dependencies (uses Django admin only)
- ✅ All email sends logged to database for audit trail

---

## Files to Create/Modify

**New:**
- `backend/apps/accounts/services.py` — send_email() function
- `backend/apps/accounts/migrations/XXXX_email_log.py` — EmailLog model
- `backend/config/admin.py` — CustomAdminSite
- `backend/templates/admin/custom_index.html` — dashboard template
- `backend/apps/accounts/tasks.py` — Celery task (optional phase 2)

**Modify:**
- `backend/apps/accounts/models.py` — add EmailLog
- `backend/apps/accounts/admin.py` — add EmailLogAdmin, actions, register custom site
- `backend/config/urls.py` — use custom admin site
- `backend/apps/accounts/views.py` or `tasks.py` — use send_email() in registration/password reset flows

---

## Scope Notes

**Not included (post-MVP):**
- Email template A/B testing
- Bulk email campaigns
- Email unsubscribe management
- Detailed email analytics (opens, clicks)
- SMS/push notifications

These can be added in future phases.

---

## References

- Resend API docs: https://resend.com/docs/api-reference
- Django admin customization: https://docs.djangoproject.com/en/4.2/ref/contrib/admin/
- Celery beat: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html
