from PIL import Image
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext as _

STATUS_CHOICES = (('Active', 'Active'), ('Deactivated', 'Deactivated'),)
USER_RIGHTS = (('Admin', 'Admin'), ('IT_Admin', 'IT Admin'), ('User', 'User'))
USER_DEPARTMENT = (('cabin_crew', 'cabin_crew'), ('flight_crew', 'flight_crew'), ('Administration', 'Administration'),
                   ('Back_Office', 'Back Office'))


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    department = models.CharField(max_length=50, null=True, blank=True, choices=USER_DEPARTMENT)
    designation = models.CharField(max_length=50, null=True, blank=True)
    contact_number = models.CharField(max_length=20, null=True, blank=True, unique=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    date_of_birth = models.DateField(default=timezone.now)
    is_manager = models.BooleanField(default=False)
    first_line_manager = models.CharField(settings.AUTH_USER_MODEL, max_length=50, null=True, blank=True)
    second_line_manager = models.CharField(settings.AUTH_USER_MODEL, max_length=50, null=True, blank=True)
    staff_status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    staff_rights = models.CharField(max_length=50, choices=USER_RIGHTS, default='User')
    update_comments = models.CharField(max_length=500, null=True, blank=True)
    admin_password_reset = models.CharField(_('Admin Password Reset'), max_length=50, blank=True, null=True)
    user_password_reset = models.CharField(_('User Password Reset'), max_length=50, blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, default=1)
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        img = Image.open(self.image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

    def __str__(self):
        return f'{self.first_name}{" "}{self.last_name}'


class LeaveRequest(models.Model):
    # User who is requesting the leave
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='leave_requests')

    # Start and end dates for the leave
    start_date = models.DateField()
    end_date = models.DateField()

    # Reason for the leave request
    reason = models.TextField()

    # Status of the leave request
    PENDING = 'Pending'
    APPROVED = 'Approved'
    REJECTED = 'Rejected'
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (REJECTED, 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    # Date when the leave request was made
    request_date = models.DateTimeField(default=timezone.now)
    # Manager's comments regarding the leave request
    manager_comments = models.TextField(blank=True, null=True)
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='leave_request_added_by', )
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)

    def __str__(self):
        return f'Leave Request by {self.user.first_name} {self.user.last_name} from {self.start_date} to {self.end_date}'

    def save(self, *args, **kwargs):
        # If the status is approved by the first approver, set the first_approver field to the user's manager
        if self.status == self.APPROVED and not self.first_approver:
            self.first_approver = self.user.reports_to
            # If the first approver has a manager, set the second_approver field
            if self.first_approver.reports_to:
                self.second_approver = self.first_approver.reports_to
        super().save(*args, **kwargs)


class CrewLicense(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='crew_license')
    crew_license_type = models.CharField(max_length=50)
    crew_license_number = models.CharField(max_length=50)
    crew_license_date_of_issue = models.DateField()
    crew_license_issuing_authority = models.CharField(max_length=50)
    crew_license_expiration_date = models.DateField()
    record_date = models.DateTimeField(default=timezone.now)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                 related_name='crew_license_added_by')
    updated_date = models.DateTimeField(_('Updated Date'), blank=True, null=True)
    updated_by = models.CharField(_('Updated By'), max_length=50, blank=True)
