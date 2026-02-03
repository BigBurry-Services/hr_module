from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
import datetime
import calendar
import csv
from .models import Employee, Attendance, Department, Designation, Allowance, EmployeeAllowance, HRProfile, Holiday, Leave, SalaryAdvance, AttendanceDevice, LeaveType, AttendanceLock, SalaryPayment, ManualSalaryAdjustment
from django.contrib.auth.models import User
from django.db import transaction
from .forms import EmployeeForm, RegistrationForm, DepartmentForm, DesignationForm, AllowanceForm, EmployeeAllowanceForm, EmployeeAllowanceFormSet, AttendanceForm, HRProfileForm, HolidayForm, LeaveForm, SalaryAdvanceForm, AttendanceDeviceForm, LeaveTypeForm, SalarySummaryForm, EmployeeDocumentFormSet
from django.http import JsonResponse
from .utils import DeviceSyncService
from .decorators import hr_required, admin_required
from decimal import Decimal
from django.db.models import Sum


@hr_required
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
    # Check dependencies
    related_allocations = EmployeeAllowance.objects.filter(allowance=allowance)
    related_count = related_allocations.count()
    
    if request.method == 'POST':
        if related_count > 0:
             # This should be caught by the template check, but as a fallback
            return render(request, 'core/allowance_confirm_delete.html', {
                'allowance': allowance,
                'related_allocations': related_allocations,
                'related_count': related_count,
                'error': "Cannot delete allowance with active assignments."
            })
        allowance.delete()
        return redirect('allowance_list')
        
    return render(request, 'core/allowance_confirm_delete.html', {
        'allowance': allowance,
        'related_allocations': related_allocations,
        'related_count': related_count
    })

@hr_required
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
    # Check dependencies
    related_employees = Employee.objects.filter(department=department)
    related_count = related_employees.count()

    if request.method == 'POST':
        # Dependencies are handled by on_delete=SET_NULL in model
        department.delete()
        messages.success(request, f"Department '{department.name}' deleted successfully.")
        return redirect('department_list')
    return render(request, 'core/department_confirm_delete.html', {
        'department': department,
        'related_employees': related_employees,
        'related_count': related_count
    })

@hr_required
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
    # Check dependencies
    related_employees = Employee.objects.filter(designation=designation)
    related_count = related_employees.count()

    if request.method == 'POST':
        # Dependencies are handled by on_delete=SET_NULL in model
        designation.delete()
        messages.success(request, f"Designation '{designation.name}' deleted successfully.")
        return redirect('designation_list')
    return render(request, 'core/designation_confirm_delete.html', {
        'designation': designation,
        'related_employees': related_employees,
        'related_count': related_count
    })

@hr_required
def dashboard(request):
    # Total employees
    total_employees = Employee.objects.count()
    
    # Birthday logic
    today = datetime.date.today()
    
    # Employees with birthdays this month
    birthdays_this_month = Employee.objects.filter(
        date_of_birth__month=today.month
    ).exclude(date_of_birth__isnull=True).order_by('date_of_birth__day')
    
    context = {
        'total_employees': total_employees,
        'birthdays_this_month': birthdays_this_month,
        'birthdays_this_month_count': birthdays_this_month.count(),
        'retiring_count': 0, # Placeholder
        'checked_in_count': Attendance.objects.filter(date=today).count(),
    }
    
    # Calculate Retiring Count (Next 90 days)
    limit_date = today + datetime.timedelta(days=90)
    retiring_count = 0
    all_employees = Employee.objects.all() # Optimization: values_list('date_of_birth') if large
    for emp in all_employees:
        if emp.date_of_birth:
            try:
                # Calculate retirement date (DOB + 58 years)
                retirement_date = emp.date_of_birth.replace(year=emp.date_of_birth.year + 58)
                if today <= retirement_date <= limit_date:
                    retiring_count += 1
            except ValueError:
                pass
    context['retiring_count'] = retiring_count
    
    return render(request, 'core/dashboard.html', context)

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                # Role-based redirect
                if hasattr(user, 'hrprofile'):
                    if user.hrprofile.role == 2: # Employee
                        return redirect('employee_dashboard')
                    else: # HR or Admin
                        return redirect('dashboard')
                elif hasattr(user, 'employee_profile'):
                     # Fallback if accessed via Employee-User link but NO HRProfile
                     return redirect('employee_dashboard')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    email=form.cleaned_data['email'],
                    password=form.cleaned_data['password']
                )
                # Create an HRProfile for the new user, defaulting to HR (Level 1)
                # User can change roles via Admin if needed
                HRProfile.objects.create(
                    user=user,
                    role=1 
                )
                messages.success(request, "Account created successfully! Please login.")
                return redirect('login')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = RegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@hr_required
def employee_list(request):
    employees = Employee.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        from django.db.models import Q
        employees = employees.filter(
            Q(full_name__icontains=search_query) |
            Q(employee_code__icontains=search_query) |
            Q(department__name__icontains=search_query) |
            Q(designation__name__icontains=search_query)
        )
    
    # Filter functionality
    filter_type = request.GET.get('filter')
    if filter_type == 'retiring':
        today = datetime.date.today()
        # Retiring age = 58
        # We look for people turning 58 in the next 90 days.
        # This means their DOB + 58 years is between today and today + 90 days.
        # Converting to DOB range: 
        # DOB >= today - 58 years
        # DOB <= today + 90 days - 58 years
        start_date_58_years_ago = today - datetime.timedelta(days=58*365.25) # Approx
        # A more precise way for "turning 58":
        # Target retirement date range: [today, today+90]
        # For each target date T, the person born on T - 58 years retires then.
        # So we look for DOB in range [today - 58y, today+90d - 58y] roughly.
        
        # Let's use strict date construction:
        # retirement_date = dob.replace(year=dob.year + 58)
        # We want today <= retirement_date <= today + 90
        
        # Accessing all and filtering in python might be safer/easier for "replace year" logic 
        # than complex DB queries unless the DB supports age calculation well.
        # For simplicity and typical small/med DB size, Python filtering is fine.
        
        filtered_ids = []
        limit_date = today + datetime.timedelta(days=90)
        
        for emp in employees:
            if emp.date_of_birth:
                try:
                    retirement_date = emp.date_of_birth.replace(year=emp.date_of_birth.year + 58)
                    if today <= retirement_date <= limit_date:
                        filtered_ids.append(emp.id)
                except ValueError:
                    # Handle leap years if any edge case (e.g. born Feb 29, 58 years later?)
                    pass
        
        employees = employees.filter(id__in=filtered_ids)
    
    # Sorting functionality
    sort_by = request.GET.get('sort', 'employee_code')  # Default sort
    order = request.GET.get('order', 'asc')
    
    # Mapping friendly sort keys to actual model fields
    sort_map = {
        'code': 'employee_code',
        'name': 'full_name',
        'department': 'department__name',
        'designation': 'designation__name',
        'date': 'joining_date'
    }
    
    # Get the actual model field, defaulting to employee_code if invalid key
    model_field = sort_map.get(sort_by, 'employee_code')
    
    if order == 'desc':
        model_field = '-' + model_field
        
    employees = employees.order_by(model_field)
    
    return render(request, 'core/employee_list.html', {
        'employees': employees,
        'search_query': search_query,
        'current_sort': sort_by,
        'current_order': order
    })

from django.forms import inlineformset_factory

@login_required
def employee_add(request):
    allowances = Allowance.objects.all()
    # Create a dynamic formset with enough extra fields for all allowances
    # We disable delete since these are mandatory
    EmployeeAllowanceFormSetDynamic = inlineformset_factory(
        Employee, 
        EmployeeAllowance, 
        form=EmployeeAllowanceForm,
        extra=len(allowances),
        can_delete=False
    )

    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        formset = EmployeeAllowanceFormSetDynamic(request.POST)
        doc_formset = EmployeeDocumentFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid() and doc_formset.is_valid():
            try:
                with transaction.atomic():
                    employee = form.save()
                    formset.instance = employee
                    formset.save()
                    doc_formset.instance = employee
                    doc_formset.save()
                    messages.success(request, "Employee added successfully.")
                    return redirect('employee_list')
            except Exception as e:
                print(f"Error saving employee: {e}")
                messages.error(request, f"System Error: {str(e)}")
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)
            print("Doc Formset Errors:", doc_formset.errors)
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()
        initial_allowances = [{'allowance': a, 'amount': 0} for a in allowances]
        formset = EmployeeAllowanceFormSetDynamic(queryset=EmployeeAllowance.objects.none(), initial=initial_allowances)
        doc_formset = EmployeeDocumentFormSet()
        
    return render(request, 'core/employee_form.html', {
        'form': form, 
        'formset': formset,
        'doc_formset': doc_formset
    })

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'core/employee_detail.html', {'employee': employee})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    allowances = Allowance.objects.all()

    # Ensure this employee has a record for every allowance (default to 0)
    for allowance in allowances:
        EmployeeAllowance.objects.get_or_create(
            employee=employee,
            allowance=allowance,
            defaults={'amount': 0}
        )
    
    # Use standard formset but with 0 extra, as we just created all necessary records
    EmployeeAllowanceFormSetFixed = inlineformset_factory(
        Employee, 
        EmployeeAllowance, 
        form=EmployeeAllowanceForm,
        extra=0,
        can_delete=False
    )

    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        formset = EmployeeAllowanceFormSetFixed(request.POST, instance=employee)
        doc_formset = EmployeeDocumentFormSet(request.POST, request.FILES, instance=employee)
        if form.is_valid() and formset.is_valid() and doc_formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    doc_formset.save()
                    messages.success(request, f"Employee {employee.full_name} updated locally.")
                    return redirect('employee_list')
            except Exception as e:
                print(f"Error updating employee: {e}")
                messages.error(request, f"System Error: {str(e)}")
        else:
             print("Edit Form Errors:", form.errors)
             print("Edit Formset Errors:", formset.errors)
             print("Doc Formset Errors:", doc_formset.errors)
             messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm(instance=employee)
        formset = EmployeeAllowanceFormSetFixed(instance=employee)
        doc_formset = EmployeeDocumentFormSet(instance=employee)
        
    return render(request, 'core/employee_form.html', {
        'form': form, 
        'formset': formset,
        'doc_formset': doc_formset
    })

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')
    return render(request, 'core/employee_confirm_delete.html', {'employee': employee})

@hr_required
def attendance_mark(request):
    departments = Department.objects.all()
    
    # Filter variables
    selected_dept_id = request.GET.get('department')
    search_query = request.GET.get('search', '')
    
    today = datetime.date.today()
    selected_year = int(request.GET.get('year', today.year))
    selected_month = int(request.GET.get('month', today.month))
    selected_date_str = request.GET.get('date')

    if selected_date_str:
        try:
            # Handle flexible date strings (e.g., 2026-1-1 or 2026-01-01)
            if '-' in selected_date_str:
                parts = selected_date_str.split('-')
                selected_date = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
            else:
                selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
            # Ensure year/month consistency if date is passed
            selected_year = selected_date.year
            selected_month = selected_date.month
        except (ValueError, IndexError):
            selected_date = today
            selected_date_str = selected_date.strftime('%Y-%m-%d')
    else:
        # Default to today if current month/year, else the 1st
        if selected_year == today.year and selected_month == today.month:
            selected_date = today
        else:
            selected_date = datetime.date(selected_year, selected_month, 1)
        selected_date_str = selected_date.strftime('%Y-%m-%d')

    # Get Employees based on filter
    employees = Employee.objects.all()
    if selected_dept_id:
        employees = employees.filter(department_id=selected_dept_id)
        
    if search_query:
        from django.db.models import Q
        employees = employees.filter(
            Q(full_name__icontains=search_query) | 
            Q(employee_code__icontains=search_query)
        )

    # Pre-fetch existing attendance for the selected date to show status
    existing_attendance = Attendance.objects.filter(date=selected_date)
    attendance_map = {att.employee_id: att for att in existing_attendance}

    error_message = None
    success_message = None

    if request.method == 'POST':
        action = request.POST.get('action')  # 'check_in' or 'check_out'
        employee_ids = request.POST.getlist('employee_ids')
        time_value = request.POST.get('time')
        notes = request.POST.get('notes', '')
        
        if not employee_ids:
            error_message = "Please select at least one employee."
        elif not time_value:
            error_message = "Please enter a time."
        elif action == 'check_in':
            # Check-in: Create or update attendance with check_in_time
            count = 0
            for emp_id in employee_ids:
                Attendance.objects.update_or_create(
                    employee_id=emp_id,
                    date=selected_date,
                    defaults={
                        'check_in_time': time_value,
                        'is_manual': True,
                        'notes': notes
                    }
                )
                count += 1
            success_message = f"Successfully checked in {count} employee(s)."
            
        elif action == 'check_out':
            # Check-out: Validate that employee has checked in, then update check_out_time
            count = 0
            not_checked_in = []
            
            for emp_id in employee_ids:
                try:
                    attendance = Attendance.objects.get(employee_id=emp_id, date=selected_date)
                    # Employee has checked in, update check_out_time
                    attendance.check_out_time = time_value
                    attendance.is_manual = True
                    if notes:
                        attendance.notes = notes
                    attendance.save()
                    count += 1
                except Attendance.DoesNotExist:
                    # Employee hasn't checked in yet
                    emp = Employee.objects.get(id=emp_id)
                    not_checked_in.append(emp.full_name)
            
            if not_checked_in:
                error_message = f"Cannot check out - not checked in: {', '.join(not_checked_in)}"
            else:
                success_message = f"Successfully checked out {count} employee(s)."
        
        # Get Attendance Map
    existing_attendance = Attendance.objects.filter(date=selected_date)
    attendance_map = {att.employee_id: att for att in existing_attendance}

    # Get Leave Map
    existing_leaves = Leave.objects.filter(start_date__lte=selected_date, end_date__gte=selected_date)
    leave_map = {leave.employee_id: leave for leave in existing_leaves}

    # Get Leave Types
    leave_types = LeaveType.objects.all()

    # Check if month is locked (Check if ANY employee is locked, or check specific logic)
    # Check if month is locked (Check if ANY employee is locked, or check specific logic)
    is_month_locked = AttendanceLock.objects.filter(
        month=selected_month,
        year=selected_year,
        is_locked=True,
        date__isnull=True
    ).exists()

    # Check if current day is locked
    is_day_locked = AttendanceLock.objects.filter(
        date=selected_date,
        is_locked=True
    ).exists()

    # Check if ALL days of the month are locked to enable the "Lock Month" button
    # Get number of days in selected month
    num_days = calendar.monthrange(selected_year, selected_month)[1]
    locked_days_count = AttendanceLock.objects.filter(
        month=selected_month,
        year=selected_year,
        is_locked=True,
        date__isnull=False
    ).values('date').distinct().count()
    
    can_lock_month = (locked_days_count == num_days)

    # Calendar Data
    cal_weeks = calendar.monthcalendar(selected_year, selected_month)
    holidays_this_month = Holiday.objects.filter(date__year=selected_year, date__month=selected_month)
    holiday_days = [h.date.day for h in holidays_this_month]
    
    # Get day locks for the entire month for the calendar grid
    month_day_locks = AttendanceLock.objects.filter(
        month=selected_month,
        year=selected_year,
        is_locked=True,
        date__isnull=False
    ).values_list('date__day', flat=True).distinct()

    context = {
        'departments': departments,
        'employees': employees,
        'attendance_map': attendance_map,
        'leave_map': leave_map,
        'leave_types': leave_types,
        'selected_dept_id': int(selected_dept_id) if selected_dept_id else None,
        'selected_date': selected_date_str,
        'selected_day': selected_date.day,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'month_name': calendar.month_name[selected_month],
        'calendar_weeks': cal_weeks,
        'holiday_days': holiday_days,
        'search_query': search_query,
        'current_time': datetime.datetime.now().strftime('%H:%M'),
        'error_message': error_message,
        'success_message': success_message,
        'is_month_locked': is_month_locked,
        'is_day_locked': is_day_locked,
        'can_lock_month': can_lock_month,
        'month_day_locks': list(month_day_locks),
        'years': range(today.year - 2, today.year + 2),
        'months': list(enumerate(calendar.month_name))[1:]
    }
    return render(request, 'core/attendance_mark.html', context)

@hr_required
def mark_single_leave(request, employee_id):
    if request.method == 'POST':
        try:
            employee = get_object_or_404(Employee, pk=employee_id)
            date_str = request.POST.get('date')
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Check if attendance exists
            if Attendance.objects.filter(employee=employee, date=date_obj).exists():
                messages.error(request, f"Cannot mark leave. Employee {employee.full_name} is marked present.")
                return redirect(f"{reverse('attendance_mark')}?date={date_str}")

            # Cleanup existing leaves for this day to allow override/edit
            # This handles the "editable" requirement by removing the old one before adding new
            Leave.objects.filter(employee=employee, start_date__lte=date_obj, end_date__gte=date_obj).delete()
            
            # Get Selected Leave Type
            # The input name is dynamic: leave_type_{employee_id}
            selected_type_id = request.POST.get(f'leave_type_{employee.id}')
            
            leave_category = "Paid" # Default
            reason = "Marked by HR"
            
            if selected_type_id == 'unpaid':
                 leave_category = "Unpaid"
                 reason = "Unpaid Leave - Marked by HR"
                 # We don't link a LeaveType for purely ad-hoc unpaid leave unless needed, 
                 # or we could make a dummy 'Unpaid' LeaveType. 
                 # For now, we just set the category.
            elif selected_type_id:
                 try:
                     lt = LeaveType.objects.get(pk=selected_type_id)
                     reason = f"{lt.name} - Marked by HR"
                     # Logic to determine if it's Paid/Unpaid based on LeaveType properties could go here
                     # For now assuming defined types are Paid unless specified otherwise
                 except LeaveType.DoesNotExist:
                     pass
            else:
                 # Default fallback if nothing selected
                 leave_category = "Paid" 
                 reason = "Casual Leave - Marked by HR"

            Leave.objects.create(
                employee=employee,
                start_date=date_obj,
                end_date=date_obj,
                leave_type=leave_category,
                reason=reason,
                status='Approved'
            )
            messages.success(request, f"Leave marked for {employee.full_name}.")
        except Exception as e:
            messages.error(request, f"Error marking leave: {e}")
            
        return redirect(f"{reverse('attendance_mark')}?date={request.POST.get('date', '')}")
    return redirect('attendance_mark')

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

@hr_required
def attendance_sync(request):
    """
    Redirects to the device list since management is now handled there.
    Kept for backward compatibility or future aggregation.
    """
    return redirect('device_list')

@hr_required
def device_list(request):
    devices = AttendanceDevice.objects.all()
    if request.method == 'POST':
        form = AttendanceDeviceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('device_list')
    else:
        form = AttendanceDeviceForm()
    return render(request, 'core/device_list.html', {'devices': devices, 'form': form})

@login_required
def device_edit(request, pk):
    device = get_object_or_404(AttendanceDevice, pk=pk)
    if request.method == 'POST':
        form = AttendanceDeviceForm(request.POST, instance=device)
        if form.is_valid():
            form.save()
            return redirect('device_list')
    else:
        form = AttendanceDeviceForm(instance=device)
    return render(request, 'core/device_edit.html', {'form': form})

@login_required
def device_delete(request, pk):
    device = get_object_or_404(AttendanceDevice, pk=pk)
    if request.method == 'POST':
        device.delete()
        return redirect('device_list')
    return render(request, 'core/device_confirm_delete.html', {'device': device})

@login_required
def device_test_connection(request, pk):
    device = get_object_or_404(AttendanceDevice, pk=pk)
    status_msg = ""
    error_msg = ""
    
    try:
        from zk import ZK
        zk = ZK(device.ip_address, port=device.port, timeout=5)
        conn = zk.connect()
        status_msg = f"Successfully connected to {device.name} ({device.ip_address})!"
        
        # Update last activity
        device.last_activity = datetime.datetime.now()
        device.save()
        
        conn.disconnect()
    except Exception as e:
        error_msg = f"Failed to connect: {str(e)}"
    
    # Pass context to list view or render a status page
    # For simplicity, we'll re-render the list with a message
    devices = AttendanceDevice.objects.all()
    form = AttendanceDeviceForm()
    context = {
        'devices': devices,
        'form': form,
        'status_msg': status_msg,
        'error_msg': error_msg
    }
    return render(request, 'core/device_list.html', context)


@hr_required
def summary(request):
    # Initialize form with POST or GET data
    if request.method == 'POST':
        form = SalarySummaryForm(request.POST)
    elif request.GET.get('employee'):
        # Check if we have GET params to prepopulate and auto-submit
        form = SalarySummaryForm(request.GET)
    else:
        form = SalarySummaryForm()
        
    summary_data = None
    is_month_locked = False
    is_salary_paid = False

    # Helper to format seconds to HH:MM
    def format_seconds(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours:02d}:{minutes:02d}"

    # Verify logic applies to both POST and valid GET
    if form.is_valid():
        month = int(form.cleaned_data['month'])
        year = int(form.cleaned_data['year'])
        employee = form.cleaned_data['employee']

        is_month_locked = AttendanceLock.objects.filter(
            month=month,
            year=year,
            is_locked=True,
            date__isnull=True
        ).exists()

        # Check Salary Payment Lock
        is_salary_paid = False
        salary_payment = SalaryPayment.objects.filter(employee=employee, month=month, year=year).first()
        if salary_payment and salary_payment.is_paid:
            is_salary_paid = True

        # Default action to generate if via GET
        action = request.POST.get('action', 'generate')
        
        # Use the selected year
        current_year = year

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
        
        # Holiday Logic: Holidays are Paid Days
        holidays_qs = Holiday.objects.filter(date__range=[start_date, end_date])
        holiday_set = {h.date for h in holidays_qs}
        holiday_map = {h.date: h.description for h in holidays_qs}
        
        
        # --- REFACTORED LOGIC START ---

        # 1. Fetch Leaves for the Map (needed for the loop)
        leave_map = {}
        if employee:
             leaves = Leave.objects.filter(
                 employee=employee,
                 start_date__lte=end_date, 
                 end_date__gte=start_date,
                 status='Approved'
             )
             for l in leaves:
                 curr = l.start_date
                 while curr <= l.end_date:
                     if start_date <= curr <= end_date:
                         leave_map[curr] = l.leave_type
                     curr += datetime.timedelta(days=1)

        # 2. Main Attendance Loop (Calculate Time & Build List)
        full_attendance_list = []
        att_map = {att.date: att for att in attendance_records}
        
        total_regular_seconds = 0
        total_overtime_seconds = 0
        present_days_count = 0
        unpaid_leaves_count = 0
        paid_leaves_count = 0 # NEW
        
        for day in range(1, num_days + 1):
            current_date = datetime.date(current_year, month, day)
            record = att_map.get(current_date)
            
            day_data = {
                'date': current_date,
                'check_in_time': "Not Done",
                'check_out_time': "Not Done",
                'notes': "",
                'check_in_alert': True,
                'check_out_alert': True,
                'working_hours': "-",
                'overtime': "-",
                'is_low_hours': False,
                'status': "Absent",
                'status_color': 'danger', 
                'id': None,
                'no_break': False
            }
            
            is_present = False
            if record:
                is_present = True
                day_data['id'] = record.id
                day_data['no_break'] = record.no_break
                
                if current_date in holiday_map:
                    day_data['status'] = f"Present (Holiday)"
                else:
                    day_data['status'] = "Present"
                day_data['status_color'] = "success"
                
                if record.check_in_time:
                    day_data['check_in_time'] = record.check_in_time
                    day_data['check_in_alert'] = False
                
                if record.check_out_time:
                    day_data['check_out_time'] = record.check_out_time
                    day_data['check_out_alert'] = False
                
                day_data['notes'] = record.notes if record.notes else ""

                if record.check_in_time and record.check_out_time:
                    check_in = datetime.datetime.combine(current_date, record.check_in_time)
                    check_out = datetime.datetime.combine(current_date, record.check_out_time)
                    
                    if check_out < check_in:
                        check_out += datetime.timedelta(days=1)
                    
                    duration = check_out - check_in
                    raw_seconds = duration.total_seconds()
                    
                    if raw_seconds > 0:
                        present_days_count += 1
                    
                    deduction = 3600
                    if record.no_break:
                        deduction = 0
                    
                    seconds = raw_seconds - deduction
                    if seconds < 0: seconds = 0
                    
                    if seconds < 14400:
                        day_data['is_low_hours'] = True
                    
                    if current_date in holiday_map:
                        day_data['working_hours'] = "08:00"
                        day_data['overtime'] = format_seconds(seconds)
                        day_data['check_in_time'] = f"{day_data.get('check_in_time', '')} (Holiday)"
                        day_data['check_out_time'] = f"{day_data.get('check_out_time', '')} (Holiday)"
                        total_regular_seconds += 28800
                        total_overtime_seconds += seconds
                    else:
                        if seconds > 28800:
                            regular_seconds = 28800
                            ot_seconds = seconds - 28800
                            day_data['working_hours'] = format_seconds(regular_seconds)
                            day_data['overtime'] = format_seconds(ot_seconds)
                            total_regular_seconds += regular_seconds
                            total_overtime_seconds += ot_seconds
                        else:
                            day_data['working_hours'] = format_seconds(seconds)
                            day_data['overtime'] = "00:00"
                            total_regular_seconds += seconds

            if not is_present:
                if current_date in leave_map:
                    l_type = leave_map[current_date]
                    day_data['status'] = f"On Leave ({l_type})"
                    day_data['status_color'] = "warning"
                    if l_type == 'Paid':
                        paid_leaves_count += 1 # Track count
                        seconds = 28800
                        day_data['working_hours'] = "08:00 (Leave)"
                        total_regular_seconds += seconds
                    elif l_type == 'Unpaid':
                         unpaid_leaves_count += 1

                elif current_date in holiday_map:
                    day_data['status'] = f"Holiday ({holiday_map[current_date]})"
                    day_data['status_color'] = "info"
                    day_data['working_hours'] = "08:00"
                    day_data['check_in_time'] = "Holiday"
                    day_data['check_out_time'] = "Holiday"
                    day_data['check_in_alert'] = False
                    day_data['check_out_alert'] = False
                    total_regular_seconds += 28800

            full_attendance_list.append(day_data)

        # 3. Calculate Salary Components using Central Function
        calc_data = calculate_salary_for_month(employee, month, year)
        
        basic_salary = calc_data['basic'] or Decimal('0.00')
        daily_wage = basic_salary / 30 if basic_salary > 0 else Decimal('0.00')
        per_minute_wage = (daily_wage / Decimal(480)).quantize(Decimal("0.01")) if basic_salary > 0 else Decimal('0.00')
        
        earned_basic = calc_data['basic_regular'] if 'basic_regular' in calc_data else calc_data['earned_basic']
        overtime_amount = calc_data['overtime_amount']
        gross_salary = calc_data['total_salary']
        pf = calc_data['pf']
        esi = calc_data['esic']
        employer_pf = calc_data['employer_pf']
        employer_esi = calc_data['employer_esi']
        pf_eligible = basic_salary <= 15000
        esi_eligible = basic_salary <= 21000

        # --- SUMMARY FORM OVERRIDES (Top Priority & Persistence) ---
        manual_pf = form.cleaned_data.get('manual_pf')
        manual_esi = form.cleaned_data.get('manual_esi')

        # Persist to ManualSalaryAdjustment if it's a POST request (Manual Save)
        if request.method == 'POST' and not is_salary_paid:
            adjustment, created = ManualSalaryAdjustment.objects.get_or_create(
                employee=employee, month=month, year=year
            )
            adjustment.pf_override = manual_pf
            adjustment.esi_override = manual_esi
            adjustment.save()

        if manual_pf is not None:
             pf = manual_pf
             employer_pf = manual_pf # 1:1 for manual
             pf_eligible = True
             
        if manual_esi is not None:
             esi = manual_esi
             employer_esi = manual_esi * (Decimal('3.25') / Decimal('0.75')) # 4.33 ratio
             esi_eligible = True

        # --- SNAPSHOT OVERRIDE (If Paid) ---
        if is_salary_paid and salary_payment:
             pf = salary_payment.pf_deduction
             esi = salary_payment.esi_deduction
             employer_pf = salary_payment.employer_pf
             employer_esi = salary_payment.employer_esi
             form.fields['manual_pf'].initial = pf
             form.fields['manual_esi'].initial = esi

        # Salary Advance
        advances = SalaryAdvance.objects.filter(employee=employee, date__range=[start_date, end_date])
        total_advance = advances.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        
        # Allowance List (Needed for Summary UI)
        total_allowances = 0
        allowance_list = []
        if employee:
            emp_allowances = employee.employeeallowance_set.select_related('allowance').all()
            for emp_allowance in emp_allowances:
                amount = emp_allowance.amount
                total_allowances += amount
                allowance_list.append({
                    'name': emp_allowance.allowance.name,
                    'amount': amount
                })

        total_deductions = pf + esi + total_advance + (calc_data.get('leave_cut_amount', 0))
        salary_payable = gross_salary - total_deductions

        # Salary Advance
        advances = SalaryAdvance.objects.filter(employee=employee, date__range=[start_date, end_date])
        total_advance = advances.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        # Leave Cut Calculation (for display)
        # We want to show FULL Basic in Earnings, and Leave Cut in Deductions.
        # Logic: 
        # Earned Basic = Actual Pay for time worked.
        # Leave Cut = Full Basic - Earned Basic.
        leave_cut_amount = basic_salary - earned_basic
        if leave_cut_amount < 0: leave_cut_amount = 0 # Should not happen unless extra pay?

        # For Display on Slip:
        # Gross Salary (Display) = Full Basic + Allowances + Overtime
        # Total Deductions (Display) = PF + ESI + Advance + Leave Cut
        # Net Pay = Gross (Display) - Total Deductions (Display)
        
        # Original Logic Result:
        # Net Pay = (Earned Basic + Allowances + OT) - (PF + ESI + Advance)
        
        # Verify Math:
        # Net Pay (Display) = (Full Basic + Allowances + OT) - (PF + ESI + Advance + (Full Basic - Earned Basic))
        #                   = Full Basic + All + OT - PF - ESI - Adv - Full Basic + Earned Basic
        #                   = Earned Basic + All + OT - PF - ESI - Adv
        #                   = Original Net Pay
        # So math holds.
        
        # We will use these new "Display" variables for the context passed to template/PDF.

        display_gross_salary = basic_salary + total_allowances + overtime_amount
        display_total_deductions = pf + esi + total_advance + leave_cut_amount
        
        # Re-assign standard variables to use these display values where appropriate, 
        # OR keep 'gross_salary' as 'Earned Gross' for other logic?
        # The view passes 'gross_salary' and 'total_deductions' to template.
        # User wants SLIP to show these. So we update them.
        
        gross_salary = display_gross_salary
        total_deductions = display_total_deductions
        
        salary_payable = gross_salary - total_deductions

        # --- PAYMENT LOCK LOGIC ---
        if action == 'unlock':
            unlock_password = request.POST.get('unlock_password', '')
            if unlock_password == '1234':
                if salary_payment:
                    salary_payment.is_paid = False
                    salary_payment.save()
                    is_salary_paid = False
                    messages.warning(request, f"Salary for {employee.full_name} has been UNLOCKED.")
                    return redirect(f"{request.path}?employee={employee.id}&month={month}&year={year}")
            else:
                messages.error(request, "Incorrect Password. Cannot unlock salary.")
        
        elif action == 'mark_paid' and not is_salary_paid:
             SalaryPayment.objects.update_or_create(
                 employee=employee, month=month, year=year,
                 defaults={
                     'amount': salary_payable,
                     'gross_salary': gross_salary,
                     'net_salary': salary_payable,
                     'pf_deduction': pf,
                     'esi_deduction': esi,
                     'employer_pf': employer_pf,
                     'employer_esi': employer_esi,
                     'leave_deduction': leave_cut_amount,
                     'salary_advance': total_advance,
                     'is_paid': True
                 }
             )
             is_salary_paid = True
             messages.success(request, f"Salary for {employee.full_name} marked as PAID.")
             # Redirect to prevent re-submission
             return redirect(f"{request.path}?employee={employee.id}&month={month}&year={year}")

        if is_salary_paid:
             # Override with Payment Snapshot
             gross_salary = salary_payment.gross_salary
             salary_payable = salary_payment.net_salary
             pf = salary_payment.pf_deduction
             esi = salary_payment.esi_deduction
             employer_pf = salary_payment.employer_pf
             employer_esi = salary_payment.employer_esi
             leave_cut_amount = salary_payment.leave_deduction
             total_advance = salary_payment.salary_advance
             
             total_deductions = pf + esi + total_advance + leave_cut_amount
        
        total_pf_contribution = pf + employer_pf
        total_esi_contribution = esi + employer_esi
        total_emp_share = pf + esi
        total_employer_share = employer_pf + employer_esi
        grand_total_gov_payable = total_emp_share + total_employer_share
        
        # Absents
        # paid_days_count logic is now moot for salary calc, but maybe useful for display?
        # We calculated present_days_count.
        # We have paid leaves in the loop.
        # Let's reconstruct absent days.
        # absent = total_days - (present + paid_leaves + holidays)
        # Actually easier: absent = total_days - paid_days_count
        # We need to sum "Paid Days" properly if we want to show it.
        # But the loop logic handles status.
        # A simpler absent count: count days where status is 'Absent'.
        # But we didn't track that explicitly in a counter.
        # Re-calc 'Paid Days' for absent count?
        # Previous logic: paid_days = distinct union of present/holiday/paid-leave.
        
        # Let's derive absent from the loop for consistency
        # absent = days where status == 'Absent'.
        absent_days_count = 0
        for d in full_attendance_list:
             if d['status'] == 'Absent':
                 absent_days_count += 1
        
        total_pf_contribution = pf + employer_pf
        total_esi_contribution = esi + employer_esi
        total_emp_share = pf + esi
        total_employer_share = employer_pf + employer_esi
        grand_total_gov_payable = total_emp_share + total_employer_share
        
        # Prepare Slip Data
        earnings_list_slip = []
        earnings_list_slip.append({"name": "Basic Salary", "amount": basic_salary})
        # If overtime_amount is handled separately in calc_data, show it.
        # Otherwise, if it's 0 (because it was folded into basic), it shows 0.
        earnings_list_slip.append({"name": "Overtime Allowance", "amount": overtime_amount})
        
        for al in allowance_list:
             earnings_list_slip.append({"name": al['name'], "amount": al['amount']})
        
        deductions_list_slip = []
        deductions_list_slip.append({"name": "Salary Advance", "amount": total_advance})
        if esi_eligible:
            deductions_list_slip.append({"name": "ESIC (0.75%)", "amount": esi})
        if pf_eligible:
            deductions_list_slip.append({"name": "PF", "amount": pf})
        
        if leave_cut_amount > 0:
            deductions_list_slip.append({"name": "Leave Cut", "amount": leave_cut_amount})
            
        slip_rows = []
        max_rows = max(len(earnings_list_slip), len(deductions_list_slip))
        
        for i in range(max_rows):
            e_item = earnings_list_slip[i] if i < len(earnings_list_slip) else None
            d_item = deductions_list_slip[i] if i < len(deductions_list_slip) else None
            
            row = {
                'earning_name': e_item['name'].upper() if e_item else "",
                'earning_amount': e_item['amount'] if e_item else "",
                'deduction_name': d_item['name'].upper() if d_item else "",
                'deduction_amount': d_item['amount'] if d_item else ""
            }
            slip_rows.append(row)

        summary_data = {
            'employee_name': employee.full_name if employee else "All Employees",
            'employee_code': employee.employee_code if employee else "-",
            'month': start_date.strftime("%B %Y"),
            'total_working_days': total_working_days,
            'total_present_days': present_days_count,
            'total_absent_days': absent_days_count,
            'total_working_hours': format_seconds(calc_data['total_regular_seconds']),
            'total_overtime_hours': format_seconds(calc_data['total_overtime_seconds']),
            'total_minutes_worked': calc_data['total_minutes_worked'],
            'total_gross_hours': format_seconds(calc_data['total_grand_seconds']), # NEW field
            
            'basic_salary': basic_salary,
            'earned_basic': earned_basic,
            'overtime_amount': overtime_amount,
            'pf_eligible': pf_eligible,
            'esi_eligible': esi_eligible,
            'total_allowances': total_allowances,
            'allowance_list': allowance_list,
            'gross_salary': gross_salary,
            'pf': pf,
            'esi': esi,
            'employer_pf': employer_pf,
            'employer_esi': employer_esi,
            'total_pf_contribution': total_pf_contribution,
            'total_esi_contribution': total_esi_contribution,
            'total_emp_share': total_emp_share,
            'total_employer_share': total_employer_share,
            'grand_total_gov_payable': grand_total_gov_payable,
            'salary_advance': total_advance,
            'total_deductions': total_deductions,
            'salary_payable': salary_payable,
            'daily_wage': daily_wage,
            'per_minute_wage': per_minute_wage,
            
             'designation': employee.designation.name if employee and employee.designation else "N/A",
             'joining_date': employee.joining_date if employee else None,
             'pf_number': employee.pf_number if employee else "-",
             'esi_number': employee.esi_number if employee else "-",
             'leave_cut_days': unpaid_leaves_count,
             'leave_cut_amount': leave_cut_amount,
             'total_unpaid_leaves': unpaid_leaves_count,
             'total_paid_leaves': paid_leaves_count, # NEW Field
             'slip_rows': slip_rows,
             
             'attendance_list': full_attendance_list
        }

        if action == 'download_pdf':
            response = HttpResponse(content_type='application/pdf')
            fname = f"Salary_Slip_{employee.full_name}_{start_date.strftime('%b_%Y')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{fname}"'
            
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch

            doc = SimpleDocTemplate(response, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = styles["Heading1"]
            title_style.alignment = 1 # Center
            elements.append(Paragraph(f"Salary Slip - {summary_data['month']}", title_style))
            elements.append(Paragraph("ASHIQ ENTERPRISES", styles["Heading2"])) # Assuming company name
            elements.append(Spacer(1, 0.2*inch))
            
            # 1. Employee Details Table
            emp_data = [
                ["Employee Name:", summary_data['employee_name'], "Employee Code:", summary_data.get('code', employee.employee_code)],
                ["Designation:", summary_data.get('designation', '-'), "Date of Joining:", str(summary_data.get('joining_date', '-'))],
                ["PF Number:", summary_data.get('pf_number', '-'), "ESI Number:", summary_data.get('esi_number', '-')]
            ]
            t_emp = Table(emp_data, colWidths=[1.5*inch, 2.5*inch, 1.5*inch, 1.5*inch])
            t_emp.setStyle(TableStyle([
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,0), (-1,-1), 10),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'), # Labels Bold
                ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'), # Labels Bold
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
            ]))
            elements.append(t_emp)
            elements.append(Spacer(1, 0.2*inch))
            
            # 2. Attendance Summary
            # User Req: Remove Present/Absent. Fix Paid Leaves.
            att_data = [
                ["Working Days", "Unpaid Leaves"],
                [
                    str(summary_data['total_working_days']),
                    str(summary_data['total_unpaid_leaves'])
                ]
            ]
            # Add Hours row
            att_data.append(["Total Hours", "OT Hours", "Total Minutes"])
            att_data.append([
                str(summary_data['total_working_hours']),
                str(summary_data['total_overtime_hours']),
                 str(summary_data['total_minutes_worked'])
            ])
            
            t_att = Table(att_data, colWidths=[3.5*inch]*2) # Adjusted widths for 2 columns
            t_att.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey), # Header
                ('BACKGROUND', (0,2), (-1,2), colors.lightgrey), # Header 2
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTNAME', (0,2), (-1,2), 'Helvetica-Bold'),
            ]))
            elements.append(t_att)
            elements.append(Spacer(1, 0.2*inch))
            
            # 3. Salary Details (Earnings vs Deductions side-by-side)
            
            # Build Earnings List
            earnings_list = []
            # CHANGED: Use Full Basic
            earnings_list.append(["Basic Salary", f"{summary_data['basic_salary']:.2f}"])
            earnings_list.append(["Overtime Amount", f"{summary_data['overtime_amount']:.2f}"])
            for al in summary_data['allowance_list']:
                earnings_list.append([al['name'], f"{al['amount']:.2f}"])
            # Fill with empty rows to match deductions if needed? No, separate inner tables inside a master table.
            
            # Build Deductions List
            deductions_list = []
            deductions_list.append(["PF (Employee)", f"{summary_data['pf']:.2f}"])
            deductions_list.append(["ESI (Employee)", f"{summary_data['esi']:.2f}"])
            deductions_list.append(["Salary Advance", f"{summary_data['salary_advance']:.2f}"])
            # Leave Cut
            if summary_data.get('leave_cut_amount', 0) > 0:
                 deductions_list.append(["Leave Cut", f"{summary_data['leave_cut_amount']:.2f}"])
            
            # Totals
            gross_row = ["GROSS EARNINGS", f"{summary_data['gross_salary']:.2f}"]
            deduct_row = ["TOTAL DEDUCTIONS", f"{summary_data['total_deductions']:.2f}"]
            
            # We construct two tables and place them side by side
            
            # Pad lists to same length for better alignment (optional but good layout)
            max_rows = max(len(earnings_list), len(deductions_list))
            while len(earnings_list) < max_rows: earnings_list.append(["", ""])
            while len(deductions_list) < max_rows: deductions_list.append(["", ""])
            
            earnings_data = [["EARNINGS", "AMOUNT"]] + earnings_list + [gross_row]
            deductions_data = [["DEDUCTIONS", "AMOUNT"]] + deductions_list + [deduct_row]
            
            t_earn = Table(earnings_data, colWidths=[2.5*inch, 1.0*inch])
            t_earn.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'), # Amount Right Align
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'), # Total Row Bold
                ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
            ]))
            
            t_deduct = Table(deductions_data, colWidths=[2.5*inch, 1.0*inch])
            t_deduct.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (1,0), (1,-1), 'RIGHT'),
                ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
                ('BACKGROUND', (0,-1), (-1,-1), colors.whitesmoke),
            ]))
            
            # Master Table for Side-by-Side
            t_master = Table([[t_earn, t_deduct]], colWidths=[3.75*inch, 3.75*inch])
            t_master.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ]))
            elements.append(t_master)
            elements.append(Spacer(1, 0.2*inch))
            
            # 4. Net Salary
            net_style = ParagraphStyle('NetPay', parent=styles['Heading2'], alignment=1, textColor=colors.darkblue)
            elements.append(Paragraph(f"NET SALARY PAYABLE: {summary_data['salary_payable']:.2f}", net_style))
            
            elements.append(Spacer(1, 0.3*inch))
            
            # Signatures
            sig_data = [["Employee Signature", "", "Employer Signature"]]
            t_sig = Table(sig_data, colWidths=[2.5*inch, 2.5*inch, 2.5*inch])
            t_sig.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('TOPPADDING', (0,0), (-1,-1), 40), # Space for signature
            ]))
            elements.append(t_sig)
            
            # --- New Page: Daily Attendance ---
            from reportlab.platypus import PageBreak
            elements.append(PageBreak())
            
            elements.append(Paragraph(f"Daily Attendance Log - {summary_data['month']}", title_style))
            elements.append(Spacer(1, 0.2*inch))
            
            # Columns: Date, Day, Check In, Check Out, Working Hrs, OT, Status
            daily_data = [["Date", "Day", "Check In", "Check Out", "Working Hrs", "OT", "Status"]]
            
            for att in summary_data['attendance_list']:
                # Format Date: D-M-Y
                d_str = att['date'].strftime("%d-%m-%Y")
                day_name = att['date'].strftime("%A")
                
                # Check In/Out - handle potential None or Special string
                # summary.html uses: {{ row.check_in_time|time:"H:i" }} or "Not Done"
                # att dict has 'check_in_time' as time obj or string "Not Done"
                def fmt_time(t):
                    if isinstance(t, (datetime.time, datetime.datetime)):
                        return t.strftime("%H:%M")
                    return str(t)

                cin = fmt_time(att['check_in_time'])
                cout = fmt_time(att['check_out_time'])
                
                # Status
                status = att['status']
                
                daily_data.append([
                    d_str, 
                    day_name, 
                    cin, 
                    cout, 
                    str(att['working_hours']), 
                    str(att['overtime']), 
                    status
                ])

            t_daily = Table(daily_data, colWidths=[1.0*inch, 1.2*inch, 1.0*inch, 1.0*inch, 1.0*inch, 0.8*inch, 1.2*inch])
            
            # Striped Table Style
            ts_daily = [
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('BACKGROUND', (0,0), (-1,0), colors.darkgrey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTSIZE', (0,0), (-1,-1), 9),
            ]
            
            # Row stripes
            for i in range(1, len(daily_data)):
                if i % 2 == 0:
                    bg = colors.whitesmoke
                else:
                    bg = colors.white
                ts_daily.append(('BACKGROUND', (0,i), (-1,i), bg))
                
                # Highlight Absent/Leave
                stat = daily_data[i][6] # status column
                if 'Absent' in stat or 'Unpaid' in stat:
                     ts_daily.append(('TEXTCOLOR', (6,i), (6,i), colors.red))
                elif 'Paid' in stat or 'Holiday' in stat:
                     ts_daily.append(('TEXTCOLOR', (6,i), (6,i), colors.green))

            t_daily.setStyle(TableStyle(ts_daily))
            elements.append(t_daily)

            doc.build(elements)
            return response


    context = {
        'form': form,
        'summary_data': summary_data,
        'is_month_locked': is_month_locked,
        'is_salary_paid': is_salary_paid,
        'disabled_status': 'disabled' if is_salary_paid else '',
        'selected_month': form.cleaned_data['month'] if form.is_valid() else None,
        'selected_year': form.cleaned_data['year'] if form.is_valid() else None,
        'selected_employee_id': employee.id if 'employee' in locals() and employee else None
    }
    return render(request, 'core/summary.html', context)

@hr_required
def toggle_attendance_lock(request):
    """
    Toggles the lock status for an employee (or all) for a specific month/year.
    """
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        month = request.POST.get('month')
        year = request.POST.get('year')
        date_str = request.POST.get('date')
        
        # Validate inputs
        if (month and year) or date_str:
            if date_str:
                date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                month = date_obj.month
                year = date_obj.year
            else:
                date_obj = None
                month = int(month)
                year = int(year)
            
            employees_to_lock = []
            if employee_id:
                employees_to_lock.append(get_object_or_404(Employee, pk=employee_id))
            elif request.POST.get('lock_all') == 'true':
                 # Requirement: month lock button enables when every day of that month is locked.
                 # If it's a month lock (date_obj is None), double check if all days are locked for extra safety
                 if not date_obj and 'unlock' not in request.POST:
                     num_days = calendar.monthrange(year, month)[1]
                     locked_days_count = AttendanceLock.objects.filter(
                         month=month,
                         year=year,
                         is_locked=True,
                         date__isnull=False
                     ).values('date').distinct().count()
                     
                     if locked_days_count < num_days:
                         messages.error(request, "Cannot lock month. All days must be locked first.")
                         return redirect(request.POST.get('next') or 'summary')

                 employees_to_lock = Employee.objects.all()
            
            # Optimized Bulk Locking/Unlocking
            target_status = 'unlock' not in request.POST
            action_msg = "Unlocked" if not target_status else "Locked"

            if 'unlock' in request.POST:
                password = request.POST.get('unlock_password')
                if password != '1234':
                    messages.error(request, "Incorrect password. Unlocking denied.")
                    if request.POST.get('next'):
                         return redirect(request.POST.get('next'))
                    return redirect('summary')

            # 1. Update existing locks
            existing_locks = AttendanceLock.objects.filter(
                employee__in=employees_to_lock,
                date=date_obj,
                month=month,
                year=year
            )
            existing_employee_ids = set(existing_locks.values_list('employee_id', flat=True))
            existing_locks.update(is_locked=target_status)

            # 2. Create missing locks
            new_locks = []
            for employee in employees_to_lock:
                if employee.id not in existing_employee_ids:
                    new_locks.append(AttendanceLock(
                        employee=employee,
                        date=date_obj,
                        month=month,
                        year=year,
                        is_locked=target_status
                    ))
            
            if new_locks:
                AttendanceLock.objects.bulk_create(new_locks)
            
            # --- Automated Month Lock/Unlock Logic ---
            if date_obj: # Only trigger if we modified a day-level lock
                if 'unlock' in request.POST:
                    # If any day is unlocked, auto-unlock the month
                    AttendanceLock.objects.filter(
                        month=month,
                        year=year,
                        date__isnull=True
                    ).update(is_locked=False)
                    # Note: We don't show a separate message for this as it's a side effect.
                else:
                    # If locking a day, check if ALL days in month are now locked
                    num_days = calendar.monthrange(year, month)[1]
                    locked_days_count = AttendanceLock.objects.filter(
                        month=month,
                        year=year,
                        is_locked=True,
                        date__isnull=False
                    ).values('date').distinct().count()
                    
                    if locked_days_count == num_days:
                        # Auto-lock month for all employees
                        for emp in Employee.objects.all():
                            mlock, _ = AttendanceLock.objects.get_or_create(
                                employee=emp,
                                date=None,
                                month=month,
                                year=year
                            )
                            mlock.is_locked = True
                            mlock.save()
                        messages.info(request, f"Month {calendar.month_name[month]} {year} has been automatically finalized and locked.")
            # ------------------------------------------

            if employees_to_lock:
                if len(employees_to_lock) > 1:
                     msg = f"{action_msg} attendance for all employees ({month}/{year})"
                else:
                     msg = f"{action_msg} attendance for {employees_to_lock[0]} ({month}/{year})"
                messages.success(request, msg)
            else:
                 messages.warning(request, "No employees selected to lock.")

            # Redirect logic
            if request.POST.get('next'):
                 return redirect(request.POST.get('next'))
            
            # Default redirect to summary if not specified
            base_url = reverse('summary')
            if employee_id:
                query_string = f"?employee={employee_id}&month={month}&year={year}"
                return redirect(base_url + query_string)
            return redirect(base_url)
        
    return redirect('summary')
        
    return redirect('summary')

@login_required
def export_employees_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Employee Code', 
        'Full Name', 
        'Department', 
        'Designation', 
        'Joining Date', 
        'Mobile',
        'Address',
        'Date of Birth',
        'Aadhar Number',
        'Sex',
        'Nationality',
        'State',
        'Previous Experience',
        'Employment Type',
        'Basic Salary',
        'PF Number',
        'ESI Number'
    ])

    employees = Employee.objects.all()
    for emp in employees:
        writer.writerow([
            emp.employee_code,
            emp.full_name,
            emp.department.name if emp.department else 'N/A',
            emp.designation.name if emp.designation else 'N/A',
            emp.joining_date,
            emp.contact_number,
            emp.address,
            emp.date_of_birth,
            emp.aadhar_number,
            emp.sex,
            emp.nationality,
            emp.state,
            emp.previous_experience,
            emp.employment_type,
            emp.basic_salary,
            emp.pf_number,
            emp.esi_number,
        ])

    return response

@login_required
def export_single_employee_csv(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    response = HttpResponse(content_type='text/csv')
    filename = f"employee_{employee.employee_code}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow([
        'Employee Code', 
        'Full Name', 
        'Department', 
        'Designation', 
        'Joining Date', 
        'Mobile',
        'Address',
        'Date of Birth',
        'Aadhar Number',
        'Sex',
        'Nationality',
        'State',
        'Previous Experience',
        'Employment Type',
        'Basic Salary',
        'PF Number',
        'ESI Number'
    ])

    writer.writerow([
        employee.employee_code,
        employee.full_name,
        employee.department.name if employee.department else 'N/A',
        employee.designation.name if employee.designation else 'N/A',
        employee.joining_date,
        employee.contact_number,
        employee.address,
        employee.date_of_birth,
        employee.aadhar_number,
        employee.sex,
        employee.nationality,
        employee.state,
        employee.previous_experience,
        employee.employment_type,
        employee.basic_salary,
        employee.pf_number,
        employee.esi_number,
    ])

    return response

@login_required
def export_attendance_csv(request):
    selected_dept_id = request.GET.get('department')
    selected_date_str = request.GET.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    
    try:
        selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.date.today()

    response = HttpResponse(content_type='text/csv')
    filename = f"attendance_{selected_date}_{selected_dept_id or 'all'}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Employee Code', 'Employee Name', 'Department', 'Check In', 'Check Out', 'Notes'])

    # Filter Attendance
    attendance_records = Attendance.objects.filter(date=selected_date)
    if selected_dept_id:
        attendance_records = attendance_records.filter(employee__department_id=selected_dept_id)
        
    for att in attendance_records:
        writer.writerow([
            att.date,
            att.employee.employee_code,
            att.employee.full_name,
            att.employee.department.name if att.employee.department else 'N/A',
            att.check_in_time,
            att.check_out_time,
            att.notes
        ])

    return response

@hr_required
def export_monthly_attendance_csv(request):
    """
    Exports monthly attendance data for selected employees in CSV format.
    Supports single employee from summary page or multiple from monthly report.
    """
    month = int(request.GET.get('month') or request.POST.get('month') or datetime.date.today().month)
    year = int(request.GET.get('year') or request.POST.get('year') or datetime.date.today().year)
    
    # Get employee IDs from POST (batch) or GET (single)
    employee_ids = request.POST.getlist('employee_ids') or request.GET.getlist('employee_ids')
    
    # Fallback for single employee from summary page
    if not employee_ids and (request.GET.get('employee') or request.POST.get('employee')):
        employee_ids = [request.GET.get('employee') or request.POST.get('employee')]

    if not employee_ids:
        messages.error(request, "Please select at least one employee to export.")
        return redirect('monthly_salary_report')

    _, num_days = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)

    employees = Employee.objects.filter(id__in=employee_ids)
    
    response = HttpResponse(content_type='text/csv')
    month_name = calendar.month_name[month]
    
    if employees.count() == 1:
        emp_name = employees.first().full_name.replace(' ', '_')
        filename = f"attendance_{emp_name}_{month_name}_{year}.csv"
    else:
        filename = f"attendance_batch_{month_name}_{year}.csv"
        
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Employee Code', 'Employee Name', 'Date', 'Day', 'Check In', 'Check Out', 'Working Hours', 'Overtime', 'Status', 'Notes'])

    for emp in employees:
        att_records = Attendance.objects.filter(employee=emp, date__range=[start_date, end_date])
        att_map = {att.date: att for att in att_records}
        
        holidays_qs = Holiday.objects.filter(date__range=[start_date, end_date])
        holiday_map = {h.date: h.description for h in holidays_qs}
        
        leaves = Leave.objects.filter(employee=emp, start_date__lte=end_date, end_date__gte=start_date, status='Approved')
        leave_map = {}
        for l in leaves:
            curr = l.start_date
            while curr <= l.end_date:
                if start_date <= curr <= end_date:
                    leave_map[curr] = l.leave_type
                curr += datetime.timedelta(days=1)

        for day in range(1, num_days + 1):
            curr_date = datetime.date(year, month, day)
            record = att_map.get(curr_date)
            
            check_in = "Absent"
            check_out = "Absent"
            working_hours = "-"
            overtime = "-"
            status = "Absent"
            notes = ""

            if record:
                status = "Present"
                if curr_date in holiday_map:
                    status = f"Present (Holiday)"
                
                check_in = record.check_in_time.strftime('%H:%M') if record.check_in_time else "Not Done"
                check_out = record.check_out_time.strftime('%H:%M') if record.check_out_time else "Not Done"
                notes = record.notes or ""

                if record.check_in_time and record.check_out_time:
                    dt_in = datetime.datetime.combine(curr_date, record.check_in_time)
                    dt_out = datetime.datetime.combine(curr_date, record.check_out_time)
                    if dt_out < dt_in: dt_out += datetime.timedelta(days=1)
                    duration = (dt_out - dt_in).total_seconds()
                    
                    deduction = 3600 if not record.no_break else 0
                    seconds = duration - deduction
                    if seconds < 0: seconds = 0
                    
                    def fmt_secs(s):
                        h = int(s // 3600)
                        m = int((s % 3600) // 60)
                        return f"{h:02d}:{m:02d}"

                    if curr_date in holiday_map:
                        working_hours = "08:00"
                        overtime = fmt_secs(seconds)
                    else:
                        if seconds > 28800:
                            working_hours = "08:00"
                            overtime = fmt_secs(seconds - 28800)
                        else:
                            working_hours = fmt_secs(seconds)
                            overtime = "00:00"
            else:
                if curr_date in leave_map:
                    status = f"On Leave ({leave_map[curr_date]})"
                    if leave_map[curr_date] == 'Paid':
                        working_hours = "08:00 (Leave)"
                elif curr_date in holiday_map:
                    status = f"Holiday ({holiday_map[curr_date]})"
                    working_hours = "08:00"
                    check_in = "Holiday"
                    check_out = "Holiday"

            writer.writerow([
                emp.employee_code,
                emp.full_name,
                curr_date.strftime('%Y-%m-%d'),
                curr_date.strftime('%A'),
                check_in,
                check_out,
                working_hours,
                overtime,
                status,
                notes
            ])
        # Add an empty row between employees for readability
        writer.writerow([])

    return response

@login_required
def sync_attendance_view(request):
    if request.method == 'POST':
        try:
            target_date_str = request.POST.get('date')
            if target_date_str:
                 target_date = datetime.datetime.strptime(target_date_str, '%Y-%m-%d').date()
            else:
                 target_date = datetime.date.today()
            
            service = DeviceSyncService()
            results = service.sync_devices(target_date=target_date)
            
            # Auto-Absent Logic for Past Dates
            today = datetime.date.today()
            processed_absent = 0
            if target_date < today:
                # Ensure 'Absent' leave type exists
                absent_type, _ = LeaveType.objects.get_or_create(name="Absent", defaults={'days_allowed': 0})
                
                all_employees = Employee.objects.all()
                for emp in all_employees:
                    # Check if they have attendance
                    has_attendance = Attendance.objects.filter(employee=emp, date=target_date).exists()
                    if has_attendance:
                        continue
                        
                    # Check if they already have leave
                    has_leave = Leave.objects.filter(employee=emp, start_date__lte=target_date, end_date__gte=target_date).exists()
                    if has_leave:
                        continue
                    
                    # Create Absent Record
                    try:
                        Leave.objects.create(
                            employee=emp,
                            start_date=target_date,
                            end_date=target_date,
                            leave_type="Unpaid", # Absent is usually unpaid
                            reason="Auto-marked Absent (No Punch Record)",
                            status='Approved'
                        )
                        processed_absent += 1
                    except Exception as e:
                        print(f"Failed to auto-mark absent for {emp}: {e}")
                
                if processed_absent > 0:
                    results['message'] = results.get('message', '') + f" Also marked {processed_absent} employees as Absent."

            if results['errors']:
                return JsonResponse({'status': 'warning', 'message': 'Sync completed with errors.', 'details': results}, status=200)
            
            msg = f"Sync Complete: {results['created_count']} New, {results['updated_count']} Updated. ({results['devices_connected']} Devices)"
            if processed_absent > 0:
                msg += f" {processed_absent} Absent."

            return JsonResponse({'status': 'success', 'message': msg}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=400)

@login_required
def employee_dashboard(request):
    # Ensure this view is for employees or admins, but standard flow is for Role 2
    # If an HR tries to access, they can, but the dashboard is tailored for the user's LINKED employee record.
    
    # Try to find the linked employee record
    try:
        employee = request.user.employee_profile
    except Employee.DoesNotExist:
        # If Admin/HR accesses this but isn't an "Employee" in the table:
        if hasattr(request.user, 'hrprofile') and request.user.hrprofile.role < 2:
            messages.info(request, "You are logged in as HR/Admin. You don't have a personal employee record linked.")
            return redirect('dashboard')
            
        messages.error(request, "No employee record linked to this account.")
        return redirect('login')

    # Get recent attendance
    recent_attendance = Attendance.objects.filter(employee=employee).order_by('-date')[:10]
    
    context = {
        'employee': employee,
        'recent_attendance': recent_attendance,
    }
    return render(request, 'core/employee_dashboard.html', context)

@admin_required
def manage_hrs(request):
    profiles = HRProfile.objects.all()
    return render(request, 'core/manage_hr_list.html', {'profiles': profiles})

@admin_required
def manage_hr_add(request):
    if request.method == 'POST':
        form = HRProfileForm(request.POST)
        if form.is_valid():
            try:
                # Create User
                user = User.objects.create_user(
                    username=form.cleaned_data['username'],
                    password=form.cleaned_data['password'],
                    email=form.cleaned_data['email']
                )
                # Create Profile
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
                messages.success(request, f"User {user.username} created successfully.")
                return redirect('manage_hrs')
            except Exception as e:
                messages.error(request, f"Error creating user: {e}")
    else:
        form = HRProfileForm()
    return render(request, 'core/manage_hr_form.html', {'form': form, 'title': 'Add New User'})



@admin_required
def manage_hr_edit(request, pk):
    profile = get_object_or_404(HRProfile, pk=pk)
    if request.method == 'POST':
        form = HRProfileForm(request.POST, instance=profile)
        if form.is_valid():
            try:
                user = profile.user
                user.username = form.cleaned_data['username']
                user.email = form.cleaned_data['email']
                if form.cleaned_data['password']:
                    user.set_password(form.cleaned_data['password'])
                user.save()
                form.save()
                messages.success(request, f"User {user.username} updated successfully.")
                return redirect('manage_hrs')
            except Exception as e:
                messages.error(request, f"Error updating user: {e}")
    else:
        form = HRProfileForm(instance=profile)
    return render(request, 'core/manage_hr_form.html', {'form': form, 'title': 'Edit User'})

@admin_required
def manage_hr_delete(request, pk):
    profile = get_object_or_404(HRProfile, pk=pk)
    if request.method == 'POST':
        user = profile.user
        # Prevent self-deletion
        if request.user == user:
            messages.error(request, "You cannot delete your own account.")
            return redirect('manage_hrs')
            
        user.delete() # Cascade deletes profile
        messages.success(request, f"User {user.username} deleted successfully.")
        return redirect('manage_hrs')
    
    # Render a simple confirm page or re-use a generic one
    return render(request, 'core/hr_confirm_delete.html', {'profile': profile})

@admin_required
def toggle_user_status(request, pk):
    profile = get_object_or_404(HRProfile, pk=pk)
    if request.user == profile.user:
        messages.error(request, "You cannot block your own account.")
    else:
        user = profile.user
        user.is_active = not user.is_active
        user.save()
        status = "blocked" if not user.is_active else "activated"
        messages.success(request, f"User {user.username} has been {status}.")
    
    return redirect('manage_hrs')

@hr_required
def leave_calendar(request):
    current_year = datetime.date.today().year
    current_month = datetime.date.today().month
    
    month_param = request.GET.get('month')
    year_param = request.GET.get('year')
    
    if month_param:
        current_month = int(month_param)
    if year_param:
        current_year = int(year_param)
        
    # Handle Year Rollover
    while current_month > 12:
        current_month -= 12
        current_year += 1
    while current_month < 1:
        current_month += 12
        current_year -= 1
        
    holidays = Holiday.objects.filter(date__year=current_year, date__month=current_month)
    holiday_map = {h.date.day: h for h in holidays}
    
    cal = calendar.monthcalendar(current_year, current_month)
    
    context = {
        'calendar': cal,
        'current_month': current_month,
        'current_year': current_year,
        'month_name': calendar.month_name[current_month],
        'holiday_map': holiday_map,
        'years': range(current_year - 2, current_year + 3),
        'months': list(enumerate(calendar.month_name))[1:]
    }
    return render(request, 'core/leave_calendar.html', context)

@hr_required
def toggle_holiday(request):
    import json
    if request.method == 'POST':
        try:
             data = json.loads(request.body)
             date_str = data.get('date')
             date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
             # Toggle
             holiday = Holiday.objects.filter(date=date_obj).first()
             if holiday:
                 holiday.delete()
                 status = 'removed'
             else:
                 Holiday.objects.create(date=date_obj, description="Holiday")
                 status = 'added'
             return JsonResponse({'status': 'success', 'action': status})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error'})

@hr_required
def leave_list(request):
    leave_types = LeaveType.objects.all().order_by('name')
    
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Leave Type added successfully")
            return redirect('leave_list')
    else:
        form = LeaveTypeForm()

    context = {
        'leave_types': leave_types, 
        'form': form,
    }

    return render(request, 'core/leave_list.html', context)

@hr_required
def leave_type_edit(request, pk):
    leave_type = get_object_or_404(LeaveType, pk=pk)
    if request.method == 'POST':
        form = LeaveTypeForm(request.POST, instance=leave_type)
        if form.is_valid():
            form.save()
            messages.success(request, f"Leave Type '{leave_type.name}' updated successfully.")
            return redirect('leave_list')
    else:
        form = LeaveTypeForm(instance=leave_type)
    return render(request, 'core/leave_type_edit.html', {'form': form, 'leave_type': leave_type})

@hr_required
def leave_type_delete(request, pk):
    leave_type = get_object_or_404(LeaveType, pk=pk)
    # Check dependencies
    # Since Leave model stores leave_type as a CharField (choice/string) in implementation plan analysis 
    # but let's check the model definition again.
    # Ah, the model definition showed `leave_type = models.CharField`. It DOES NOT ForeignKey to LeaveType.
    # However, for data integrity, we might want to check if any leaves use this NAME?
    # Or maybe we should improve the Leave model to use FK? 
    # For now, based on existing code, it seems decoupled or loosely coupled.
    # Re-reading model: `class LeaveType` exists. `class Leave` has `leave_type` as CharField.
    # So deleting a LeaveType won't CASCADE delete Leaves, but it might make them refer to a non-existent type definition.
    
    # Check if any Leave uses this name pattern?
    # Or just warn.
    
    # Wait, the prompt implies "leave_type" in Leave model might store the CATEGORY (Paid/Unpaid) or the TYPE NAME?
    # In `mark_single_leave` I implemented storing `reason="{Type Name} - Marked by HR"`.
    # And `leave_type` field in `Leave` model has choices 'Paid'/'Unpaid'.
    # So `LeaveType` is more like a configuration for "Days Allowed" and available names.
    
    if request.method == 'POST':
        leave_type.delete()
        messages.success(request, f"Leave Type '{leave_type.name}' deleted successfully.")
        return redirect('leave_list')
        
    return render(request, 'core/leave_type_confirm_delete.html', {'leave_type': leave_type})

@hr_required
def export_leaves_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="leave_types.csv"'

    writer = csv.writer(response)
    writer.writerow(['Leave Name', 'Days Allowed'])

    leave_types = LeaveType.objects.all().order_by('name')
    
    for lt in leave_types:
        writer.writerow([
            lt.name,
            lt.days_allowed
        ])

    return response

@hr_required
def salary_advance_list(request):
    employees = Employee.objects.all()
    
    # Filter Logic
    current_date = datetime.date.today()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))

    advances = SalaryAdvance.objects.filter(
        date__month=selected_month, 
        date__year=selected_year
    )
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        from django.db.models import Q
        advances = advances.filter(
            Q(employee__full_name__icontains=search_query) |
            Q(employee__employee_code__icontains=search_query)
        )
        
    advances = advances.order_by('-date')
    
    if request.method == 'POST':
        form = SalaryAdvanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Salary Advance added successfully")
            return redirect('salary_advance_list')
    else:
        form = SalaryAdvanceForm()
        
    context = {
        'advances': advances, 
        'employees': employees, 
        'form': form,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'months': list(enumerate(calendar.month_name))[1:],
        'years': range(current_date.year - 2, current_date.year + 3),
        'search_query': search_query
    }
        
    return render(request, 'core/salary_advance_list.html', context)

@hr_required
def export_salary_advances_csv(request):
    current_date = datetime.date.today()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))

    response = HttpResponse(content_type='text/csv')
    filename = f"salary_advances_{selected_month}_{selected_year}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Employee Name', 'Date', 'Amount', 'Reason'])

    advances = SalaryAdvance.objects.filter(
        date__month=selected_month, 
        date__year=selected_year
    ).order_by('-date')
    
    for adv in advances:
        writer.writerow([
            adv.employee.full_name,
            adv.date.strftime('%Y-%m-%d'),
            adv.amount,
            adv.reason
        ])

    return response

def calculate_salary_for_month(employee, month, year):
    """
    Helper to calculate salary components for an employee for a specific month.
    Used by monthly_salary_report and toggle_salary_status.
    Returns a dict with calculated values.
    """
    _, num_days = calendar.monthrange(year, month)
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, num_days)
    
    holidays_qs = Holiday.objects.filter(date__range=[start_date, end_date])
    holiday_set = {h.date for h in holidays_qs}
    
    # Leaves
    leaves = Leave.objects.filter(employee=employee, start_date__lte=end_date, end_date__gte=start_date, status='Approved')
    
    basic = employee.basic_salary
    if not basic: basic = Decimal(0)
    daily_rate = basic / Decimal(30)
    
    # Overtime & Presence
    att_records = Attendance.objects.filter(employee=employee, date__range=[start_date, end_date])
    total_regular_seconds = 0
    total_overtime_seconds = 0
    
    att_map = {att.date: att for att in att_records}
    leave_map = {}
    for leaves_req in leaves:
            c = max(leaves_req.start_date, start_date)
            e = min(leaves_req.end_date, end_date)
            current = c
            while current <= e:
                leave_map[current] = leaves_req.leave_type
                current += datetime.timedelta(days=1)

    current_iter_date = start_date
    while current_iter_date <= end_date:
        day_record = att_map.get(current_iter_date)
        has_record = day_record is not None
        
        if day_record and day_record.check_in_time and day_record.check_out_time:
                check_in = datetime.datetime.combine(current_iter_date, day_record.check_in_time)
                check_out = datetime.datetime.combine(current_iter_date, day_record.check_out_time)
                if check_out < check_in: check_out += datetime.timedelta(days=1)
                
                raw_seconds = (check_out - check_in).total_seconds()
                if raw_seconds > 0:
                    deduction = 3600
                    if day_record.no_break: deduction = 0
                    seconds = raw_seconds - deduction
                    if seconds < 0: seconds = 0
                    
                    if current_iter_date in holiday_set:
                        total_regular_seconds += 28800
                        total_overtime_seconds += seconds
                    else:
                        if seconds > 28800:
                            total_regular_seconds += 28800
                            total_overtime_seconds += (seconds - 28800)
                        else:
                            total_regular_seconds += seconds

        if not has_record:
                if current_iter_date in leave_map:
                    l_type = leave_map[current_iter_date]
                    if l_type == 'Paid':
                        total_regular_seconds += 28800
                elif current_iter_date in holiday_set:
                    total_regular_seconds += 28800
        
        current_iter_date += datetime.timedelta(days=1)

    total_grand_seconds = total_regular_seconds + total_overtime_seconds
    total_minutes_worked = int(total_grand_seconds / 60)
    
    ot_h = int(total_overtime_seconds // 3600)
    ot_m = int((total_overtime_seconds % 3600) // 60)
    overtime_hours_str = f"{ot_h:02d}:{ot_m:02d}"
    
    per_minute_wage = Decimal(0)
    if basic > 0:
        per_minute_wage = (daily_rate / Decimal(480)).quantize(Decimal("0.01"))
    
    ot_minutes = int(total_overtime_seconds / 60)
    total_earned = Decimal(total_minutes_worked) * per_minute_wage
    ot_amount = Decimal(ot_minutes) * per_minute_wage
    earned_basic_regular = total_earned - ot_amount
    total_allowances = sum([ea.amount for ea in employee.employeeallowance_set.all()])
    gross_salary = total_earned + total_allowances
    
    pf = Decimal(0)
    esi = Decimal(0)
    if basic <= 15000: pf = total_earned * Decimal('0.12')
    if basic <= 21000: esi = gross_salary * Decimal('0.0075')

    # Apply Manual Overrides
    try:
        adjustment = ManualSalaryAdjustment.objects.get(employee=employee, month=month, year=year)
        if adjustment.pf_override is not None:
            pf = adjustment.pf_override
        if adjustment.esi_override is not None:
            esi = adjustment.esi_override
    except ManualSalaryAdjustment.DoesNotExist:
        pass

    advances_total = SalaryAdvance.objects.filter(employee=employee, date__range=[start_date, end_date]).aggregate(sum=Sum('amount'))['sum'] or 0
    total_deductions = pf + esi + advances_total
    
    leave_cut_amount = basic - earned_basic_regular
    if leave_cut_amount < 0: leave_cut_amount = 0
    
    # Calculate unpaid leave days for display
    unpaid_leave_days = 0
    for leave in leaves:
        l_start = max(leave.start_date, start_date)
        l_end = min(leave.end_date, end_date)
        curr = l_start
        while curr <= l_end:
             if leave.leave_type == 'Unpaid': unpaid_leave_days += 1
             curr += datetime.timedelta(days=1)
             
    # Calculate working hours str
    working_hours_decimal = total_regular_seconds / 3600.0
    wh_hours = int(working_hours_decimal)
    wh_minutes = int((working_hours_decimal - wh_hours) * 60)
    total_working_hours_str = f"{wh_hours:02d}:{wh_minutes:02d}"
    earned_basic = total_earned

    return {
        'basic': basic,
        'earned_basic': earned_basic,
        'allowances': total_allowances,
        'overtime_hours': overtime_hours_str,
        'overtime_amount': ot_amount,
        'salary_advance': advances_total,
        'esic': esi,
        'pf': pf,
        'leaves': unpaid_leave_days,
        'leave_cut_amount': leave_cut_amount,
        'working_hours': total_working_hours_str,
        'total_salary': gross_salary,
        'net_salary': gross_salary - total_deductions,
        'total_deductions': total_deductions,
        # Raw Time Data
        'total_minutes_worked': total_minutes_worked,
        'total_regular_seconds': total_regular_seconds,
        'total_overtime_seconds': total_overtime_seconds,
        'total_grand_seconds': total_grand_seconds,
        # Helper fields for saving
        'gross_salary': gross_salary, 
        'salary_payable': gross_salary - total_deductions,
        'pf_deduction': pf,
        'esi_deduction': esi,
        'employer_pf': pf if ManualSalaryAdjustment.objects.filter(employee=employee, month=month, year=year, pf_override__isnull=False).exists() else (earned_basic * Decimal('0.12') if basic <= 15000 else Decimal('0.00')),
        'employer_esi': (esi * (Decimal('3.25') / Decimal('0.75'))) if ManualSalaryAdjustment.objects.filter(employee=employee, month=month, year=year, esi_override__isnull=False).exists() else (gross_salary * Decimal('0.0325') if basic <= 21000 else Decimal('0.00')),
        'leave_deduction': leave_cut_amount,
        'salary_advance': advances_total,
    }

def get_monthly_report_rows(employees, month, year):
    """
    Generates the list of report rows for the Monthly Salary Report.
    Handles Live Calculation + Snapshot Override.
    """
    # Fetch snapshots (including unpaid/unlocked ones)
    all_payments = SalaryPayment.objects.filter(month=month, year=year)
    payment_map = {p.employee_id: p for p in all_payments}
    
    report_data = []
    
    for emp in employees:
        # 1. Calculate Live Data (Hours, default money)
        data = calculate_salary_for_month(emp, month, year)
        
        # 2. Override with Snapshot if exists (For Money fields)
        payment_snapshot = payment_map.get(emp.id)
        is_paid = payment_snapshot.is_paid if payment_snapshot else False
        
        if is_paid:
            # Override money fields from snapshot ONLY if paid
            data['pf'] = payment_snapshot.pf_deduction
            data['esic'] = payment_snapshot.esi_deduction
            data['leave_cut_amount'] = payment_snapshot.leave_deduction
            data['salary_advance'] = payment_snapshot.salary_advance
            data['total_salary'] = payment_snapshot.gross_salary
            data['net_salary'] = payment_snapshot.net_salary
        
        report_data.append({
            'emp_id': emp.pk,
            'code': emp.employee_code,
            'name': emp.full_name,
            'basic': data['basic'],
            'allowances': data['allowances'],
            'overtime_hours': data['overtime_hours'],
            'overtime_amount': round(data['overtime_amount'], 2),
            'salary_advance': data['salary_advance'],
            'esic': round(data['esic'], 2),
            'pf': round(data['pf'], 2),
            'leaves': data['leaves'],
            'leave_cut_amount': round(data['leave_cut_amount'], 2),
            'working_hours': data['working_hours'],
            'total_salary': round(data['total_salary'], 2),
            'net_salary': round(data['net_salary'], 2),
            'is_paid': is_paid
        })
    return report_data

@hr_required
def monthly_salary_report(request):
    current_date = datetime.date.today()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))
    
    _, num_days = calendar.monthrange(selected_year, selected_month)
    start_date = datetime.date(selected_year, selected_month, 1)
    end_date = datetime.date(selected_year, selected_month, num_days)
    
    holidays_qs = Holiday.objects.filter(date__range=[start_date, end_date])
    holiday_set = {h.date for h in holidays_qs}
    holidays_count = holidays_qs.count()
    working_days_in_month = num_days - holidays_count
    if working_days_in_month <= 0: working_days_in_month = 1
    
    # Filter Logic
    payment_status = request.GET.get('payment_status', 'locked') # locked, all, unpaid
    
    # Identify Paid IDs for filtering
    paid_employee_ids = list(SalaryPayment.objects.filter(
        month=selected_month, year=selected_year, is_paid=True
    ).values_list('employee_id', flat=True))
    
    if payment_status == 'locked':
        employees = Employee.objects.filter(id__in=paid_employee_ids)
    elif payment_status == 'unpaid':
        employees = Employee.objects.exclude(id__in=paid_employee_ids)
    else: # all
        employees = Employee.objects.all()
    
    # Generate Report Data
    report_data = get_monthly_report_rows(employees, selected_month, selected_year)

    is_month_locked = AttendanceLock.objects.filter(
        month=selected_month,
        year=selected_year,
        is_locked=True,
        date__isnull=True
    ).exists()

    # Calculate Totals
    totals = {
        'basic': sum(d['basic'] for d in report_data),
        'allowances': sum(d['allowances'] for d in report_data),
        'overtime_amount': sum(d['overtime_amount'] for d in report_data),
        'salary_advance': sum(d['salary_advance'] for d in report_data),
        'esic': sum(d['esic'] for d in report_data),
        'pf': sum(d['pf'] for d in report_data),
        'leave_cut_amount': sum(d['leave_cut_amount'] for d in report_data),
        'total_salary': sum(d['total_salary'] for d in report_data),
        'net_salary': sum(d['net_salary'] for d in report_data),
    }

    context = {
        'report_data': report_data,
        'totals': totals,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'payment_status': payment_status,
        'is_status_locked': payment_status == 'locked',
        'is_status_all': payment_status == 'all',
        'is_status_unpaid': payment_status == 'unpaid',
        'is_month_locked': is_month_locked,
        'months': list(enumerate(calendar.month_name))[1:],
        'years': range(current_date.year - 2, current_date.year + 3)
    }
    return render(request, 'core/monthly_salary_report.html', context)

@hr_required
def toggle_salary_status(request):
    # ... (content of toggle_salary_status)
    if request.method == 'POST':
        try:
             # ... (existing content)
            employee_id = request.POST.get('employee_id')
            month = int(request.POST.get('month'))
            year = int(request.POST.get('year'))
            action = request.POST.get('action')
            
            employee = get_object_or_404(Employee, pk=employee_id)
            
            # Preserve filter params for redirect
            payment_status = request.POST.get('payment_status', 'locked')
            redirect_url = f"{reverse('monthly_salary_report')}?month={month}&year={year}&payment_status={payment_status}"
            
            if action == 'unpay':
                password = request.POST.get('password')
                if password == '1234':
                    payment = SalaryPayment.objects.filter(employee=employee, month=month, year=year).first()
                    if payment:
                        payment.is_paid = False
                        payment.save()
                        messages.warning(request, f"Salary for {employee.full_name} UNLOCKED.")
                else:
                    messages.error(request, "Incorrect Password.")
            
            elif action == 'pay':
                # Calculate Salary Data
                data = calculate_salary_for_month(employee, month, year)
                
                pass # Already handled in update_or_create below
                
                SalaryPayment.objects.update_or_create(
                    employee=employee, month=month, year=year,
                    defaults={
                        'amount': data['salary_payable'],
                        'gross_salary': data['gross_salary'],
                        'net_salary': data['salary_payable'],
                        'pf_deduction': data['pf_deduction'],
                        'esi_deduction': data['esi_deduction'],
                        'employer_pf': data['employer_pf'],
                        'employer_esi': data['employer_esi'],
                        'leave_deduction': data['leave_deduction'],
                        'salary_advance': data['salary_advance'],
                        'is_paid': True
                    }
                )
                messages.success(request, f"Salary for {employee.full_name} marked as PAID.")
            
            return redirect(redirect_url)
            
        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('monthly_salary_report')
    
    return redirect('monthly_salary_report')

@hr_required
def export_monthly_salary_report(request):
    import csv
    from django.http import HttpResponse

    current_date = datetime.date.today()
    selected_month = int(request.GET.get('month', current_date.month))
    selected_year = int(request.GET.get('year', current_date.year))
    payment_status = request.GET.get('payment_status', 'locked')

    # Identify Paid IDs
    paid_employee_ids = list(SalaryPayment.objects.filter(
        month=selected_month, year=selected_year, is_paid=True
    ).values_list('employee_id', flat=True))
    
    if payment_status == 'locked':
        employees = Employee.objects.filter(id__in=paid_employee_ids)
    elif payment_status == 'unpaid':
        employees = Employee.objects.exclude(id__in=paid_employee_ids)
    else: # all
        employees = Employee.objects.all()

    # Generate Data
    report_data = get_monthly_report_rows(employees, selected_month, selected_year)

    # Response
    response = HttpResponse(content_type='text/csv')
    filename = f"Salary_Report_{calendar.month_name[selected_month]}_{selected_year}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    # Headers
    writer.writerow([
        'Code', 'Name', 'Basic', 'Allowances', 'Wrk Hrs', 'OT (Hrs)', 'OT Amt', 
        'Advance', 'ESIC', 'PF', 'Leaves', 'Leave Cut', 'Gross', 'Net Salary', 'Status'
    ])

    # Data Rows
    for row in report_data:
        status_str = "PAID" if row['is_paid'] else "Pending"
        writer.writerow([
            row['code'],
            row['name'],
            row['basic'],
            row['allowances'],
            row['working_hours'],
            row['overtime_hours'],
            row['overtime_amount'],
            row['salary_advance'],
            row['esic'],
            row['pf'],
            row['leaves'],
            row['leave_cut_amount'],
            row['total_salary'],
            row['net_salary'],
            status_str
        ])
    
    # Totals Row
    if report_data:
        writer.writerow([
            'TOTAL', '',
            sum(d['basic'] for d in report_data),
            sum(d['allowances'] for d in report_data),
            '', '', 
            sum(d['overtime_amount'] for d in report_data),
            sum(d['salary_advance'] for d in report_data),
            sum(d['esic'] for d in report_data),
            sum(d['pf'] for d in report_data),
            '', 
            sum(d['leave_cut_amount'] for d in report_data),
            sum(d['total_salary'] for d in report_data),
            sum(d['net_salary'] for d in report_data),
            ''
        ])

    return response

@hr_required
def toggle_no_break(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    attendance.no_break = not attendance.no_break
    attendance.is_manual = True
    attendance.save()
    
    # Redirect back to previous page
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('summary')
@hr_required
def update_single_attendance(request, employee_id):
    if request.method == 'POST':
        try:
            employee = get_object_or_404(Employee, pk=employee_id)
            date_str = request.POST.get('date')
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            
            check_in = request.POST.get(f'check_in_{employee_id}')
            check_out = request.POST.get(f'check_out_{employee_id}')
            leave_type_id = request.POST.get(f'leave_type_{employee_id}')
            
            # Check for Lock
            if AttendanceLock.objects.filter(
                employee=employee, 
                month=date_obj.month, 
                year=date_obj.year, 
                is_locked=True
            ).exists():
                messages.error(request, f"Attendance for {employee.full_name} is locked regarding {date_obj.strftime('%B %Y')}.")
                # Redirect back to prevent processing
                return redirect('attendance_mark')

            # Priority: Leave Type > Attendance Times
            # If Leave Type is selected, mark as leave and remove attendance
            if leave_type_id:
                 # Clear Attendance
                 Attendance.objects.filter(employee=employee, date=date_obj).delete()
                 
                 # Create Leave
                 # Clean up existing leaves first
                 Leave.objects.filter(employee=employee, start_date__lte=date_obj, end_date__gte=date_obj).delete()
                 
                 leave_category = "Paid"
                 reason = "Marked via Spreadsheet"
                 if leave_type_id == 'unpaid':
                     leave_category = "Unpaid"
                     reason = "Unpaid Leave"
                 else:
                     try:
                         lt = LeaveType.objects.get(pk=leave_type_id)
                         reason = lt.name
                     except LeaveType.DoesNotExist:
                         pass
                 
                 Leave.objects.create(
                    employee=employee,
                    start_date=date_obj,
                    end_date=date_obj,
                    leave_type=leave_category,
                    reason=reason,
                    status='Approved'
                 )
                 messages.success(request, f"Marked Leave for {employee.full_name}")
            
            # Logic: If NO leave selected, check if we have times to update/create
            elif check_in or check_out:
                # Clear Leave if exists
                Leave.objects.filter(employee=employee, start_date__lte=date_obj, end_date__gte=date_obj).delete()
                
                # Update/Create Attendance
                defaults = {'is_manual': True}
                if check_in: defaults['check_in_time'] = check_in
                if check_out: defaults['check_out_time'] = check_out
                
                # If updating, we need to handle partial updates or full?
                # update_or_create might not unset values if we pass None, but we are passing valid strings or empty strings?
                # request.POST.get returns '' if empty usually.
                
                attendance, created = Attendance.objects.get_or_create(
                    employee=employee,
                    date=date_obj,
                    defaults=defaults
                )
                
                if not created:
                    if check_in: attendance.check_in_time = check_in
                    if check_out: attendance.check_out_time = check_out
                    attendance.is_manual = True
                    attendance.save()
                    
                # No need to sync back to device as per requirement

                messages.success(request, f"Updated Attendance for {employee.full_name}")
                
            else:
                 # Nothing provided? logic hole?
                 # Maybe user cleared everything?
                 pass

        except Exception as e:
            msg = f"Error updating: {e}"
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
                 return JsonResponse({'status': 'error', 'message': msg}, status=500)
            messages.error(request, msg)
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax'):
             return JsonResponse({'status': 'success', 'message': 'Saved successfully'})
        return redirect(f"{reverse('attendance_mark')}?date={date_str}")
    return redirect('attendance_mark')

@hr_required
def update_manual_adjustment(request):
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        month = request.POST.get('month')
        year = request.POST.get('year')
        field = request.POST.get('field')  # 'esi' or 'pf'
        value = request.POST.get('value')
        
        if not all([employee_id, month, year, field]):
             return JsonResponse({'status': 'error', 'message': 'Missing required fields.'})
             
        try:
            employee = get_object_or_404(Employee, pk=employee_id)
            month = int(month)
            year = int(year)
            
            # Check if month is paid
            is_paid = SalaryPayment.objects.filter(employee=employee, month=month, year=year, is_paid=True).exists()
            if is_paid:
                return JsonResponse({'status': 'error', 'message': 'Cannot edit paid salary.'})

            adjustment, created = ManualSalaryAdjustment.objects.get_or_create(
                employee=employee, month=month, year=year
            )
            
            # Allow clearing values by passing empty string
            decimal_value = Decimal(value) if (value is not None and value.strip() != '') else None
            
            if field == 'esi':
                adjustment.esi_override = decimal_value
            elif field == 'pf':
                adjustment.pf_override = decimal_value
            adjustment.save()
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})
