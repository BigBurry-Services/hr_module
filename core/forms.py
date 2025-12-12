from django import forms
from .models import Employee, Attendance, Department, Designation, Allowance, AttendanceDevice, EmployeeAllowance, HRProfile
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
    class Meta:
        model = Allowance
        fields = ['name']

class EmployeeForm(forms.ModelForm):
    contact_number = forms.CharField(max_length=15, validators=[RegexValidator(r'^\d{10,15}$', message="Enter a valid contact number (10-15 digits)")])
    aadhar_number = forms.CharField(max_length=12, validators=[RegexValidator(r'^\d{12}$', message="Aadhar number must be exactly 12 digits")])
    basic_salary = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    da = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    hra = forms.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    
    # User account fields
    username = forms.CharField(max_length=150, help_text="Username for employee login")
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Leave blank to keep current password (or auto-generate if new)")

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['username'].disabled = True # Prevent username change for simplicity/security
            self.fields['password'].label = "New Password"
        elif self.instance and self.instance.pk:
            self.fields['password'].required = True # User missing, enforce creation? Or keep optional? Let's make it required if not linked.
            self.fields['username'].required = True

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if not self.instance.pk: # New employee
            if User.objects.filter(username=username).exists():
                raise ValidationError("Username already exists. Please choose another.")
        return username

    def save(self, commit=True):
        employee = super().save(commit=False)
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if commit:
            if employee.user:
                # Update existing user
                user = employee.user
                if password:
                    user.set_password(password)
                    user.save()
            else:
                # Create new user
                if User.objects.filter(username=username).exists():
                     # Fallback if race condition or logic error
                     pass 
                else:
                    user = User.objects.create_user(username=username, password=password)
                    # Assign Role 2 (Employee) - Though role is on HRProfile, we might need one?
                    # Design check: Employee login relies on linking. Core Role logic is in HRProfile.
                    # Should we create HRProfile(role=2) or just use basic User + Employee link?
                    # The login view checks `hasattr(user, 'employee_profile')` as fallback.
                    # So basic User is fine. But for consistency, let's create HRProfile(role=2) if we want "role" checking.
                    # Previous code: fallback logic exists.
                    # Let's CREATE HRProfile(role=2) to be safe and consistent.
                    HRProfile.objects.create(user=user, role=2)
                    employee.user = user
            
            employee.save()
            self.save_m2m()
        return employee

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob and dob > datetime.date.today():
            raise ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean(self):
        cleaned_data = super().clean()
        dob = cleaned_data.get('date_of_birth')
        joining_date = cleaned_data.get('joining_date')
        
        # Validate password for new users
        if not self.instance.pk and not self.cleaned_data.get('password'):
             self.add_error('password', "Password is required for new employees.")

        if dob and joining_date and joining_date < dob:
            raise ValidationError("Joining date cannot be before Date of Birth.")
        return cleaned_data

class EmployeeAllowanceForm(forms.ModelForm):
    class Meta:
        model = EmployeeAllowance
        fields = ['allowance', 'amount']
        widgets = {
            'allowance': forms.HiddenInput()
        }

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

class HRProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    email = forms.EmailField(required=False)
    
    class Meta:
        model = HRProfile
        fields = ['department', 'position', 'role']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['password'].help_text = "Leave blank to keep current password"
        self.fields['role'].label = "User Role"