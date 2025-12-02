from django import forms
from .models import Employee, Attendance, Department, Designation, Allowance
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.core.validators import MinLengthValidator

class RegistrationForm(forms.Form):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    mobile_number = forms.CharField(max_length=15)
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
    class Meta:
        model = Allowance
        fields = ['name', 'amount']

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'employee_code', 'full_name', 'address', 'date_of_birth',
            'contact_number', 'aadhar_number', 'sex', 'nationality',
            'state', 'joining_date', 'department', 'designation',
            'previous_experience', 'employment_type', 'basic_salary',
            'da', 'hra', 'allowances'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'joining_date': forms.DateInput(attrs={'type': 'date'}),
            'allowances': forms.CheckboxSelectMultiple,
        }


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['employee', 'date', 'check_in_time', 'check_out_time', 'notes']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'check_in_time': forms.TimeInput(attrs={'type': 'time'}),
            'check_out_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class SalarySummaryForm(forms.Form):
    MONTH_CHOICES = [
        (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
        (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
        (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
    ]
    month = forms.ChoiceField(choices=MONTH_CHOICES)
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=False) # Optional employee filter