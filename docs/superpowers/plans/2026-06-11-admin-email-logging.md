# Admin Email Logging & Bulk Actions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add email logging and bulk admin actions so you can resend verification emails, password resets, and manage test users during MVP testing.

**Architecture:** Create `EmailLog` model to track all sent emails, centralize email sending through a `send_email()` service function, add bulk actions to Django admin for common operations. All changes integrate with existing Resend email service.

**Tech Stack:** Django ORM, Django admin, Resend email API (existing), pytest for tests.

---

## File Structure

**Files to Create:**
- `backend/apps/accounts/services.py` — Email sending service (new)
- `backend/apps/accounts/migrations/XXXX_email_log.py` — Database migration (auto-generated)
- `backend/apps/accounts/tests/test_email_service.py` — Tests for email service (new)

**Files to Modify:**
- `backend/apps/accounts/models.py` — Add `EmailLog` model
- `backend/apps/accounts/admin.py` — Add `EmailLogAdmin`, bulk actions, update `UserAdmin`
- `backend/apps/accounts/views.py` — Update registration/password reset to use `send_email()`

---

## Task 1: Add EmailLog Model to models.py

**Files:**
- Modify: `backend/apps/accounts/models.py`

- [ ] **Step 1: Add EmailLog model to models.py**

Open `backend/apps/accounts/models.py` and add this model at the end (before the file closes):

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

- [ ] **Step 2: Verify model is syntactically correct**

Run: `cd backend && python manage.py check`
Expected: No errors about the EmailLog model

- [ ] **Step 3: Create and apply migration**

Run: `cd backend && python manage.py makemigrations accounts`
Expected: Output shows migration file created (e.g., `0009_emaillog.py`)

Run: `cd backend && python manage.py migrate accounts`
Expected: Migration applies successfully, table created

- [ ] **Step 4: Commit**

```bash
git add backend/apps/accounts/models.py backend/apps/accounts/migrations/
git commit -m "feat: add EmailLog model for email audit trail

- Create EmailLog model with status tracking and Resend message ID storage
- Track email type (verification, password_reset, test)
- Index on (user, sent_at) for fast queries
- Status field shows delivery state (pending/delivered/bounced/failed)"
```

---

## Task 2: Create Email Sending Service

**Files:**
- Create: `backend/apps/accounts/services.py`

- [ ] **Step 1: Create services.py with send_email function**

Create file `backend/apps/accounts/services.py`:

```python
"""Email sending service with audit logging."""

from django.conf import settings
from django.template.loader import render_to_string
from resend import Resend

from .models import EmailLog, User


def send_email(
    user: User,
    email_type: str,
    subject: str,
    recipient: str,
    template_data: dict,
) -> EmailLog:
    """Send email via Resend and create audit log entry.
    
    Args:
        user: User object who is receiving the email
        email_type: One of EmailLog.EmailType choices (verification, password_reset, test)
        subject: Email subject line
        recipient: Recipient email address
        template_data: Dict to pass to email template
    
    Returns:
        EmailLog object with populated resend_message_id
    
    Raises:
        Exception: If Resend API fails (email not sent)
    """
    # Render HTML template
    template_path = f"emails/{email_type}.html"
    html_body = render_to_string(template_path, template_data)
    
    # Send via Resend
    resend = Resend(api_key=settings.RESEND_API_KEY)
    response = resend.emails.send({
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": recipient,
        "subject": subject,
        "html": html_body,
    })
    
    # Create audit log entry
    email_log = EmailLog.objects.create(
        user=user,
        recipient_email=recipient,
        email_type=email_type,
        subject=subject,
        resend_message_id=response.get("id") if response else None,
        status=EmailLog.Status.PENDING,
    )
    
    return email_log
```

- [ ] **Step 2: Verify imports are available**

Run: `cd backend && python -c "from apps.accounts.services import send_email; print('OK')"`
Expected: Output is `OK` (no import errors)

- [ ] **Step 3: Commit**

```bash
git add backend/apps/accounts/services.py
git commit -m "feat: create email sending service with audit logging

- Add send_email() function that sends via Resend and logs to EmailLog
- Template rendering integrated
- Returns EmailLog object for caller tracking
- Centralizes all email operations for consistency"
```

---

## Task 3: Add EmailLogAdmin to admin.py

**Files:**
- Modify: `backend/apps/accounts/admin.py`

- [ ] **Step 1: Import EmailLog at top of admin.py**

Add to imports section:

```python
from .models import EmailLog, EmailVerificationToken, PasswordResetToken, User
```

(Update existing import if it already imports from models)

- [ ] **Step 2: Add EmailLogAdmin class before other admin classes**

Add after imports and before `@admin.register(User)`:

```python
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ("sent_at", "user", "recipient_email", "email_type", "status")
    list_filter = ("email_type", "status", "sent_at")
    search_fields = ("user__email", "recipient_email")
    readonly_fields = ("sent_at", "resend_message_id", "status_checked_at")
    ordering = ["-sent_at"]
```

- [ ] **Step 3: Verify admin loads**

Run: `cd backend && python manage.py check`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add backend/apps/accounts/admin.py
git commit -m "feat: add EmailLogAdmin for viewing email history

- View all sent emails with type, status, recipient
- Filter by email_type, status, sent_at
- Search by user email or recipient email
- Read-only display of Resend message IDs and check timestamps"
```

---

## Task 4: Add Bulk Actions to UserAdmin

**Files:**
- Modify: `backend/apps/accounts/admin.py`

- [ ] **Step 1: Add bulk action functions before UserAdmin class**

Add these functions before `class UserAdmin(DjangoUserAdmin):`:

```python
def resend_verification_email(modeladmin, request, queryset):
    """Admin action: Send verification email to selected unverified users."""
    from django.contrib import messages
    from .services import send_email
    
    count = 0
    for user in queryset.filter(email_verified=False):
        token = EmailVerificationToken.objects.create(user=user)
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
        try:
            send_email(
                user=user,
                email_type=EmailLog.EmailType.VERIFICATION,
                subject="Verify your email — Vermogenspeil",
                recipient=user.email,
                template_data={"verification_link": verification_link},
            )
            count += 1
        except Exception as e:
            messages.error(request, f"Failed to send to {user.email}: {str(e)}")
    
    messages.success(request, f"Sent {count} verification emails")

resend_verification_email.short_description = "Resend verification email to selected users"


def send_password_reset_email(modeladmin, request, queryset):
    """Admin action: Send password reset link to selected users."""
    from django.contrib import messages
    from .services import send_email
    
    count = 0
    for user in queryset:
        token = PasswordResetToken.objects.create(user=user)
        reset_link = f"{settings.FRONTEND_URL}/auth/password/reset?token={token.token}"
        try:
            send_email(
                user=user,
                email_type=EmailLog.EmailType.PASSWORD_RESET,
                subject="Reset your password — Vermogenspeil",
                recipient=user.email,
                template_data={"reset_link": reset_link},
            )
            count += 1
        except Exception as e:
            messages.error(request, f"Failed to send to {user.email}: {str(e)}")
    
    messages.success(request, f"Sent {count} password reset emails")

send_password_reset_email.short_description = "Send password reset link to selected users"


def mark_email_verified(modeladmin, request, queryset):
    """Admin action: Mark selected users as email verified."""
    from django.contrib import messages
    from django.utils import timezone
    
    updated = queryset.update(email_verified=True, email_verified_at=timezone.now())
    messages.success(request, f"Marked {updated} users as verified")

mark_email_verified.short_description = "Mark selected users as email verified"
```

- [ ] **Step 2: Add actions to UserAdmin.actions**

Find the `class UserAdmin(DjangoUserAdmin):` definition and add/update the `actions` attribute:

```python
class UserAdmin(DjangoUserAdmin):
    ordering = ("email",)
    list_display = (
        "email",
        "first_name",
        "last_name",
        "subscription_tier",
        "active_tax_year",
        "email_verified",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "subscription_tier",
        "email_verified",
        "has_fiscal_partner",
        "is_staff",
        "is_active",
    )
    search_fields = ("email", "first_name", "last_name", "auth_0_id")
    actions = [resend_verification_email, send_password_reset_email, mark_email_verified]
    
    # ... rest of UserAdmin configuration stays the same
```

- [ ] **Step 3: Verify admin loads without errors**

Run: `cd backend && python manage.py check`
Expected: No errors

- [ ] **Step 4: Test actions are visible in Django admin**

Run: `cd backend && python manage.py shell`

```python
from django.contrib.admin.sites import site
from apps.accounts.admin import UserAdmin
admin_instance = site._registry[UserAdmin.model]
print([action[0] for action in admin_instance.get_actions(None)])
```

Expected: Output includes `['resend_verification_email', 'send_password_reset_email', 'mark_email_verified', 'delete_selected']`

Exit shell: `exit()`

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts/admin.py
git commit -m "feat: add bulk admin actions for email operations

- Resend verification email to unverified users
- Send password reset link to selected users
- Mark users as email verified (for testing)
- All actions log to EmailLog automatically via send_email()
- User feedback via success/error messages"
```

---

## Task 5: Update Registration Flow to Use send_email()

**Files:**
- Modify: `backend/apps/accounts/views.py` (or wherever registration sends email)

- [ ] **Step 1: Find where verification email is sent in registration**

Search for "verification" or "send_email" in views.py:

Run: `cd backend && grep -n "EmailVerificationToken\|send_mail" apps/accounts/views.py | head -20`

- [ ] **Step 2: Replace email sending with send_email() call**

Find the registration view that creates `EmailVerificationToken` and sends email. Replace the direct `send_mail()` or Resend call with:

```python
from .services import send_email

# In your registration view/serializer, after creating EmailVerificationToken:
token = EmailVerificationToken.objects.create(user=user)
verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"

send_email(
    user=user,
    email_type=EmailLog.EmailType.VERIFICATION,
    subject="Verify your email — Vermogenspeil",
    recipient=user.email,
    template_data={"verification_link": verification_link},
)
```

- [ ] **Step 3: Test registration still works**

Run: `cd backend && python manage.py test apps.accounts.tests -v 2 -k register`
Expected: All registration tests pass

- [ ] **Step 4: Verify EmailLog entry is created**

Run: `cd backend && python manage.py shell`

```python
from apps.accounts.models import EmailLog
print(f"Total emails logged: {EmailLog.objects.count()}")
print("Recent emails:")
for log in EmailLog.objects.order_by('-sent_at')[:3]:
    print(f"  - {log.email_type} to {log.recipient_email} ({log.status})")
```

Exit: `exit()`

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts/views.py
git commit -m "refactor: use send_email() service in registration flow

- Registration now uses centralized send_email() for consistency
- All verification emails logged to EmailLog automatically
- Removes duplicate email sending code"
```

---

## Task 6: Update Password Reset Flow to Use send_email()

**Files:**
- Modify: `backend/apps/accounts/views.py`

- [ ] **Step 1: Find password reset email sending**

Run: `cd backend && grep -n "password.*reset\|PasswordReset" apps/accounts/views.py | head -20`

- [ ] **Step 2: Replace with send_email() call**

Find the password reset view/serializer that creates `PasswordResetToken` and sends email. Replace with:

```python
from .services import send_email

# In password reset view, after creating PasswordResetToken:
token = PasswordResetToken.objects.create(user=user)
reset_link = f"{settings.FRONTEND_URL}/auth/password/reset?token={token.token}"

send_email(
    user=user,
    email_type=EmailLog.EmailType.PASSWORD_RESET,
    subject="Reset your password — Vermogenspeil",
    recipient=user.email,
    template_data={"reset_link": reset_link},
)
```

- [ ] **Step 3: Test password reset flow**

Run: `cd backend && python manage.py test apps.accounts.tests -v 2 -k password`
Expected: All password reset tests pass

- [ ] **Step 4: Verify EmailLog entries**

Run: `cd backend && python manage.py shell`

```python
from apps.accounts.models import EmailLog
reset_emails = EmailLog.objects.filter(email_type='password_reset')
print(f"Password reset emails logged: {reset_emails.count()}")
```

Exit: `exit()`

- [ ] **Step 5: Commit**

```bash
git add backend/apps/accounts/views.py
git commit -m "refactor: use send_email() service in password reset flow

- Password reset emails now use centralized send_email()
- All password reset emails logged to EmailLog
- Consistent with registration email pattern"
```

---

## Task 7: Write Tests for EmailLog Model

**Files:**
- Create: `backend/apps/accounts/tests/test_email_service.py`

- [ ] **Step 1: Create test file**

Create `backend/apps/accounts/tests/test_email_service.py`:

```python
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model

from apps.accounts.models import EmailLog
from apps.accounts.services import send_email

User = get_user_model()


class EmailLogModelTests(TestCase):
    """Test EmailLog model and queries."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="TestPass123!",
            first_name="Test",
            auth_0_id="auth0|test",
            email_verified=True,
        )
    
    def test_email_log_creation(self):
        """Test EmailLog can be created with all fields."""
        log = EmailLog.objects.create(
            user=self.user,
            recipient_email="recipient@example.com",
            email_type=EmailLog.EmailType.VERIFICATION,
            subject="Test email",
            resend_message_id="test-msg-id-123",
            status=EmailLog.Status.PENDING,
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.recipient_email, "recipient@example.com")
        self.assertEqual(log.email_type, EmailLog.EmailType.VERIFICATION)
        self.assertEqual(log.status, EmailLog.Status.PENDING)
    
    def test_email_log_ordering(self):
        """Test EmailLog orders by sent_at descending."""
        log1 = EmailLog.objects.create(
            user=self.user,
            recipient_email="a@example.com",
            email_type=EmailLog.EmailType.TEST,
            subject="First",
        )
        log2 = EmailLog.objects.create(
            user=self.user,
            recipient_email="b@example.com",
            email_type=EmailLog.EmailType.TEST,
            subject="Second",
        )
        
        logs = list(EmailLog.objects.all())
        self.assertEqual(logs[0].id, log2.id)
        self.assertEqual(logs[1].id, log1.id)
    
    def test_email_log_str(self):
        """Test EmailLog __str__ format."""
        log = EmailLog.objects.create(
            user=self.user,
            recipient_email="test@example.com",
            email_type=EmailLog.EmailType.PASSWORD_RESET,
            subject="Reset",
            status=EmailLog.Status.DELIVERED,
        )
        
        self.assertEqual(
            str(log),
            "password_reset → test@example.com (delivered)"
        )


@override_settings(RESEND_API_KEY="test-key")
class SendEmailServiceTests(TestCase):
    """Test send_email() service function."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email="sender@example.com",
            password="TestPass123!",
            first_name="Sender",
            auth_0_id="auth0|sender",
            email_verified=True,
        )
    
    @patch("apps.accounts.services.render_to_string")
    @patch("apps.accounts.services.Resend")
    def test_send_email_creates_log(self, mock_resend, mock_render):
        """Test send_email creates EmailLog entry."""
        mock_render.return_value = "<p>Test email</p>"
        mock_api = MagicMock()
        mock_api.emails.send.return_value = {"id": "msg-123"}
        mock_resend.return_value = mock_api
        
        log = send_email(
            user=self.user,
            email_type=EmailLog.EmailType.TEST,
            subject="Test subject",
            recipient="test@example.com",
            template_data={"name": "Test User"},
        )
        
        self.assertIsNotNone(log.id)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.recipient_email, "test@example.com")
        self.assertEqual(log.email_type, EmailLog.EmailType.TEST)
        self.assertEqual(log.resend_message_id, "msg-123")
        self.assertEqual(log.status, EmailLog.Status.PENDING)
    
    @patch("apps.accounts.services.render_to_string")
    @patch("apps.accounts.services.Resend")
    def test_send_email_calls_resend(self, mock_resend, mock_render):
        """Test send_email calls Resend API correctly."""
        mock_render.return_value = "<p>Email body</p>"
        mock_api = MagicMock()
        mock_api.emails.send.return_value = {"id": "msg-456"}
        mock_resend.return_value = mock_api
        
        send_email(
            user=self.user,
            email_type=EmailLog.EmailType.VERIFICATION,
            subject="Verify email",
            recipient="verify@example.com",
            template_data={"link": "https://example.com/verify"},
        )
        
        mock_resend.assert_called_once()
        mock_api.emails.send.assert_called_once()
        call_args = mock_api.emails.send.call_args[0][0]
        self.assertEqual(call_args["to"], "verify@example.com")
        self.assertEqual(call_args["subject"], "Verify email")
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd backend && python manage.py test apps.accounts.tests.test_email_service -v 2`
Expected: All tests pass (7 tests)

- [ ] **Step 3: Commit**

```bash
git add backend/apps/accounts/tests/test_email_service.py
git commit -m "test: add comprehensive tests for EmailLog and send_email()

- Test EmailLog model creation, ordering, string representation
- Test send_email() creates log entries
- Test send_email() calls Resend API with correct parameters
- Mock Resend API to avoid actual email sending in tests
- All tests pass"
```

---

## Task 8: Run Full Test Suite

**Files:**
- No files changed

- [ ] **Step 1: Run all accounts app tests**

Run: `cd backend && python manage.py test apps.accounts -v 2`
Expected: All tests pass (including your new email tests + existing auth tests)

- [ ] **Step 2: Run linter on modified files**

Run: `cd backend && python -m flake8 apps/accounts/models.py apps/accounts/admin.py apps/accounts/services.py --max-line-length=100`
Expected: No style errors (or only pre-existing ones)

- [ ] **Step 3: Check admin can be accessed**

Run: `cd backend && python manage.py check`
Expected: No errors

---

## Task 9: Verify Admin Interface Works

**Files:**
- No files changed

- [ ] **Step 1: Start dev server**

Run: `cd backend && python manage.py runserver` (in background or separate terminal)

- [ ] **Step 2: Access Django admin**

Open browser: `http://localhost:8000/admin/`
Log in with superuser credentials

Expected: Admin loads successfully

- [ ] **Step 3: Navigate to EmailLog**

Click "Email logs" in admin left sidebar

Expected: You see EmailLog list page (may be empty if no emails sent yet)

- [ ] **Step 4: Navigate to Users**

Click "Users" in admin left sidebar

Expected: User list shows, and dropdown at top shows actions including:
- "Resend verification email to selected users"
- "Send password reset link to selected users"  
- "Mark selected users as email verified"

- [ ] **Step 5: Stop server**

Press Ctrl+C to stop `runserver`

---

## Summary

**What you've built:**
✅ EmailLog model for audit trail  
✅ EmailLogAdmin for viewing email history  
✅ send_email() service function for centralized email sending  
✅ Bulk admin actions (resend verification, password reset, mark verified)  
✅ Integration with existing registration and password reset flows  
✅ Comprehensive tests  

**What still needs to be done (Phase 2, post-MVP):**
- Custom admin dashboard home page with recent emails stats
- Celery task to sync delivery status from Resend
- Email template previews
- Test email sending from admin

---

## How to Use This

**You can now:**
1. Send verification email to unverified test users: Admin → Users → Select users → Action: "Resend verification email"
2. Send password reset: Admin → Users → Select users → Action: "Send password reset link"
3. View all sent emails: Admin → Email logs
4. Filter emails by type/status
5. Search emails by user or recipient
