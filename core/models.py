from django.db import models
from django.contrib.auth.models import User
import datetime

class HRProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True, null=True)
    position = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

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
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class Employee(models.Model):
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
    allowances = models.ManyToManyField(Allowance, blank=True)

    def __str__(self):
        return self.full_name

class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    check_in_time = models.TimeField()
    check_out_time = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"