from django.db import models
from django.contrib.auth.models import User
import datetime

class HRProfile(models.Model):
    ROLE_CHOICES = [
        (0, 'Admin'),
        (1, 'HR'),
        (2, 'Employee'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.IntegerField(choices=ROLE_CHOICES, default=1) # Default to HR for now to maintain backward compatibility
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def is_admin(self):
        return self.role == 0
    
    @property
    def is_hr(self):
        return self.role == 1
    
    @property
    def is_employee(self):
        return self.role == 2

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Designation(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Allowance(models.Model):
    name = models.CharField(max_length=100, unique=True)
    # amount field removed as per user request, specific amount is now in EmployeeAllowance

    def __str__(self):
        return self.name

class Employee(models.Model):
    # Link to Django User for login (Level 2)
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ('Permanent', 'Permanent'),
        ('Trainee', 'Trainee'),
        ('Contract', 'Contract'),
        ('Daily Wages', 'Daily Wages'),
        ('Internship', 'Internship'),
        ('Part-Time', 'Part-Time'),
        ('Full-Time', 'Full-Time'),
    ]

    employee_code = models.CharField(max_length=20, unique=True, default=0)
    full_name = models.CharField(max_length=255, default='')
    address = models.TextField(default='')
    date_of_birth = models.DateField(null=True, blank=True, default=None)
    contact_number = models.CharField(max_length=15, default='')
    aadhar_number = models.CharField(max_length=12, default='')
    sex = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, default=None)
    nationality = models.CharField(max_length=50, default='')
    state = models.CharField(max_length=50, default='')
    joining_date = models.DateField(default=datetime.date.today)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    designation = models.ForeignKey(Designation, on_delete=models.SET_NULL, null=True, blank=True)
    previous_experience = models.TextField(default='')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, default='Permanent')
    basic_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    allowances = models.ManyToManyField(Allowance, through='EmployeeAllowance', blank=True)
    pf_number = models.CharField(max_length=50, blank=True, null=True)
    esi_number = models.CharField(max_length=50, blank=True, null=True)
    def __str__(self):
        return f"{self.full_name} ({self.employee_code})"


class EmployeeAllowance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    allowance = models.ForeignKey(Allowance, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        unique_together = ('employee', 'allowance')
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.allowance.name}: {self.amount}"



class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(blank=True, null=True)
    no_break = models.BooleanField(default=False)
    is_manual = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('employee', 'date')

    @property
    def working_hours(self):
        if self.check_in_time and self.check_out_time:
            # Combine with dummy date to perform subtraction
            import datetime
            dummy_date = datetime.date(2000, 1, 1)
            start = datetime.datetime.combine(dummy_date, self.check_in_time)
            end = datetime.datetime.combine(dummy_date, self.check_out_time)
            if end < start:
                # Handle overnight shift if necessary (assuming same day for now, or add day)
                # But for simple time fields without dates, usually same day is assumed unless specified.
                # If end < start, it might mean next day. Let's assume same day strict for now or negative.
                # Actually, usually check-out is after check-in. If overnight, you'd need DateTimeField.
                # Simple subtraction:
                pass
            diff = end - start
            total_seconds = diff.total_seconds()
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        return "-"

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

class AttendanceDevice(models.Model):
    name = models.CharField(max_length=100, help_text="Friendly name for the device, e.g., 'Main Entrance'")
    ip_address = models.GenericIPAddressField(protocol='IPv4')
    port = models.IntegerField(default=4370)
    last_activity = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"

class Holiday(models.Model):
    date = models.DateField(unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.date} - {self.description}"

    def __str__(self):
        return f"{self.date} - {self.description}"

class LeaveType(models.Model):
    name = models.CharField(max_length=100, unique=True, help_text="e.g., Casual Leave, Medical Leave")
    days_allowed = models.PositiveIntegerField(help_text="Total days allowed per year for this leave type")

    def __str__(self):
        return f"{self.name} ({self.days_allowed} days)"

class Leave(models.Model):
    LEAVE_TYPE_CHOICES = [
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPE_CHOICES)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type} ({self.start_date} to {self.end_date})"

class AttendanceLock(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(null=True, blank=True, help_text="Specific date for day-level lock. If null, it represents a month-level lock.")
    month = models.IntegerField()
    year = models.IntegerField()
    is_locked = models.BooleanField(default=False)
    locked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('employee', 'date', 'month', 'year')

    def __str__(self):
        return f"Lock: {self.employee} - {self.month}/{self.year}"

class SalaryAdvance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.amount} on {self.date}"