from django import forms
from .models import Employee, Attendance, Department, Designation, Allowance, AttendanceDevice, EmployeeAllowance
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator, MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    mobile_number = forms.CharField(max_length=15, validators=[RegexValidator(r'^\d{10,15}$', message="Enter a valid mobile number")])
    password = forms.CharField(widget=forms.PasswordInput, validators=[MinLengthValidator(4)])
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")

        if password and password2 and password != password2:
            raise forms.ValidationError("Passwords don't match")

        return cleaned_data
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name']

class DesignationForm(forms.ModelForm):
    class Meta:
        model = Designation
        fields = ['name']

class AllowanceForm(forms.ModelForm):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    class Meta:
        model = Allowance
        fields = ['name', 'amount']

class EmployeeForm(forms.ModelForm):
    contact_number = forms.CharField(max_length=15, validators=[RegexValidator(r'^\d{10,15}$', message="Enter a valid contact number (10-15 digits)")])
    aadhar_number = forms.CharField(max_length=12, validators=[RegexValidator(r'^\d{12}$', message="Aadhar number must be exactly 12 digits")])
    basic_salary = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    da = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    hra = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    class Meta:
        model = Employee
        fields = [
            'employee_code', 'full_name', 'address', 'date_of_birth',
            'contact_number', 'aadhar_number', 'sex', 'nationality',
            'state', 'joining_date', 'department', 'designation',
            'previous_experience', 'employment_type', 'basic_salary',
            'da', 'hra'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get('date_of_birth')
        joining_date = cleaned_data.get('joining_date')

        if dob and joining_date and joining_date < dob:
            raise ValidationError("Joining date cannot be before Date of Birth.")
        return cleaned_data

class EmployeeAllowanceForm(forms.ModelForm):
    class Meta:
        model = EmployeeAllowance
        fields = ['allowance', 'amount']

from django.forms import inlineformset_factory
EmployeeAllowanceFormSet = inlineformset_factory(
    Employee, 
    EmployeeAllowance, 
    form=EmployeeAllowanceForm,
    extra=1,
    can_delete=True
)


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in_time', 'check_out_time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date > datetime.date.today():
            raise ValidationError("Attendance date cannot be in the future.")
        return date

    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get("check_in_time")
        check_out = cleaned_data.get("check_out_time")

        if check_in and check_out and check_out <= check_in:
            raise ValidationError("Check-out time must be after check-in time.")
        return cleaned_data

class AttendanceDeviceForm(forms.ModelForm):
    class Meta:
        model = AttendanceDevice
        fields = ['name', 'ip_address', 'port', 'is_active']

class SalarySummaryForm(forms.Form):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False) # Optional employee filter