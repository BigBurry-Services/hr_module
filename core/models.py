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
    da = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    hra = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    allowances = models.ManyToManyField(Allowance, through='EmployeeAllowance', blank=True)
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
    notes = models.TextField(blank=True, null=True)

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