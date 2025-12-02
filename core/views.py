from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
import datetime
import calendar
from .models import Employee, Attendance, HRProfile, Department, Designation, Allowance
from django.contrib.auth.models import User
from .forms import EmployeeForm, AttendanceForm, SalarySummaryForm, RegistrationForm, DepartmentForm, DesignationForm, AllowanceForm

@login_required
def allowance_list(request):
    allowances = Allowance.objects.all()
    if request.method == 'POST':
        form = AllowanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('allowance_list')
    else:
        form = AllowanceForm()
    return render(request, 'core/allowance_list.html', {'allowances': allowances, 'form': form})

@login_required
def allowance_edit(request, pk):
    allowance = get_object_or_404(Allowance, pk=pk)
    if request.method == 'POST':
        form = AllowanceForm(request.POST, instance=allowance)
        if form.is_valid():
            form.save()
            return redirect('allowance_list')
    else:
        form = AllowanceForm(instance=allowance)
    return render(request, 'core/allowance_edit.html', {'form': form})

@login_required
def allowance_delete(request, pk):
    allowance = get_object_or_404(Allowance, pk=pk)
    if request.method == 'POST':
        allowance.delete()
        return redirect('allowance_list')
    return render(request, 'core/allowance_confirm_delete.html', {'allowance': allowance})

@login_required
def department_list(request):
    departments = Department.objects.all()
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'core/department_list.html', {'departments': departments, 'form': form})

@login_required
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'core/department_edit.html', {'form': form})

@login_required
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        return redirect('department_list')
    return render(request, 'core/department_confirm_delete.html', {'department': department})

@login_required
def designation_list(request):
    designations = Designation.objects.all()
    if request.method == 'POST':
        form = DesignationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('designation_list')
    else:
        form = DesignationForm()
    return render(request, 'core/designation_list.html', {'designations': designations, 'form': form})

@login_required
def designation_edit(request, pk):
    designation = get_object_or_404(Designation, pk=pk)
    if request.method == 'POST':
        form = DesignationForm(request.POST, instance=designation)
        if form.is_valid():
            form.save()
            return redirect('designation_list')
    else:
        form = DesignationForm(instance=designation)
    return render(request, 'core/designation_edit.html', {'form': form})

@login_required
def designation_delete(request, pk):
    designation = get_object_or_404(Designation, pk=pk)
    if request.method == 'POST':
        designation.delete()
        return redirect('designation_list')
    return render(request, 'core/designation_confirm_delete.html', {'designation': designation})

def dashboard(request):
    return render(request, 'core/dashboard_base.html')

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            # Create an HRProfile for the new user
            HRProfile.objects.create(
                user=user
            )
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees})

@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'core/employee_add.html', {'form': form})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'core/employee_detail.html', {'employee': employee})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'core/employee_edit.html', {'form': form})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')
    return render(request, 'core/employee_confirm_delete.html', {'employee': employee})

@login_required
def attendance_mark(request):
    if request.method == 'POST':
        form = AttendanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('attendance_mark')
    else:
        form = AttendanceForm()
    attendances = Attendance.objects.all().order_by('-date', '-check_in_time')
    return render(request, 'core/attendance_mark.html', {'form': form, 'attendances': attendances})

@login_required
def attendance_edit(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('attendance_mark')
    else:
        form = AttendanceForm(instance=attendance)
    return render(request, 'core/attendance_edit.html', {'form': form})

@login_required
def attendance_delete(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    if request.method == 'POST':
        attendance.delete()
        return redirect('attendance_mark')
    return render(request, 'core/attendance_confirm_delete.html', {'attendance': attendance})

@login_required
def attendance_sync(request):
    # Placeholder for biometric sync logic
    # In a real application, this would involve processing data from a biometric device
    last_sync_time = "2025-12-01 10:00:00" # Example
    total_synced_logs = 150 # Example
    errors = [] # Example

    if request.method == 'POST':
        # Simulate sync operation
        # In reality, trigger a background task or process file upload
        last_sync_time = "2025-12-01 11:30:00" # Update after simulated sync
        total_synced_logs = 160
        # errors.append("Error: Device A not responding.") # Example error
        pass

    context = {
        'last_sync_time': last_sync_time,
        'total_synced_logs': total_synced_logs,
        'errors': errors,
    }
    return render(request, 'core/attendance_sync.html', context)

@login_required
def summary(request):
    form = SalarySummaryForm(request.POST or None)
    summary_data = None

    if request.method == 'POST' and form.is_valid():
        month = int(form.cleaned_data['month'])
        employee = form.cleaned_data['employee']
        
        # Get the current year
        current_year = datetime.date.today().year

        # Get the number of days in the selected month
        _, num_days = calendar.monthrange(current_year, month)

        # Calculate the start and end dates of the selected month
        start_date = datetime.date(current_year, month, 1)
        end_date = datetime.date(current_year, month, num_days)

        # Filter attendance records
        attendance_records = Attendance.objects.filter(date__range=[start_date, end_date])
        if employee:
            attendance_records = attendance_records.filter(employee=employee)

        # Calculate total working days, present days, absent days
        total_working_days = num_days
        present_days = attendance_records.count()
        absent_days = total_working_days - present_days

        summary_data = {
            'employee_name': employee.full_name if employee else "All Employees",
            'month': start_date.strftime("%B %Y"),
            'total_working_days': total_working_days,
            'total_present_days': present_days,
            'total_absent_days': absent_days,
        }

    context = {
        'form': form,
        'summary_data': summary_data,
    }
    return render(request, 'core/summary.html', context)