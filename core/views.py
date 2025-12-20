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
from .models import Employee, Attendance, Department, Designation, Allowance, EmployeeAllowance, HRProfile, Holiday, Leave, SalaryAdvance, AttendanceDevice, LeaveType
from django.contrib.auth.models import User
from django.db import transaction
from .forms import EmployeeForm, RegistrationForm, DepartmentForm, DesignationForm, AllowanceForm, EmployeeAllowanceForm, EmployeeAllowanceFormSet, AttendanceForm, HRProfileForm, HolidayForm, LeaveForm, SalaryAdvanceForm, AttendanceDeviceForm, LeaveTypeForm, SalarySummaryForm
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
    tomorrow = today + datetime.timedelta(days=1)
    
    # Employees with birthdays today
    birthdays_today = Employee.objects.filter(
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    ).exclude(date_of_birth__isnull=True)
    
    # Employees with birthdays tomorrow
    birthdays_tomorrow = Employee.objects.filter(
        date_of_birth__month=tomorrow.month,
        date_of_birth__day=tomorrow.day
    ).exclude(date_of_birth__isnull=True)
    
    context = {
        'total_employees': total_employees,
        'birthdays_today': birthdays_today,
        'birthdays_tomorrow': birthdays_tomorrow,
        'birthdays_today_count': birthdays_today.count(),
        'birthdays_tomorrow_count': birthdays_tomorrow.count(),
    }
    
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
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    employee = form.save()
                    formset.instance = employee
                    formset.save()
                    messages.success(request, "Employee added successfully.")
                    return redirect('employee_list')
            except Exception as e:
                print(f"Error saving employee: {e}")
                messages.error(request, f"System Error: {str(e)}")
        else:
            print("Form Errors:", form.errors)
            print("Formset Errors:", formset.errors)
            print("Formset Non-Form Errors:", formset.non_form_errors())
            messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm()
        # Pre-populate with all allowances defaulted to 0
        initial_allowances = [{'allowance': a, 'amount': 0} for a in allowances]
        formset = EmployeeAllowanceFormSetDynamic(queryset=EmployeeAllowance.objects.none(), initial=initial_allowances)
        
    return render(request, 'core/employee_form.html', {'form': form, 'formset': formset})

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
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    messages.success(request, f"Employee {employee.full_name} updated locally.")
                    return redirect('employee_list')
            except Exception as e:
                print(f"Error updating employee: {e}")
                messages.error(request, f"System Error: {str(e)}")
        else:
             print("Edit Form Errors:", form.errors)
             print("Edit Formset Errors:", formset.errors)
             messages.error(request, "Please correct the errors below.")
    else:
        form = EmployeeForm(instance=employee)
        formset = EmployeeAllowanceFormSetFixed(instance=employee)
        
    return render(request, 'core/employee_form.html', {'form': form, 'formset': formset})

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
    selected_date_str = request.GET.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    search_query = request.GET.get('search', '')

    try:
        selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.date.today()

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

    context = {
        'departments': departments,
        'employees': employees,
        'attendance_map': attendance_map,
        'leave_map': leave_map,
        'leave_types': leave_types,
        'selected_dept_id': int(selected_dept_id) if selected_dept_id else None,
        'selected_date': selected_date_str,
        'search_query': search_query,
        'current_time': datetime.datetime.now().strftime('%H:%M'),
        'error_message': error_message,
        'success_message': success_message,
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

        # 3. Calculate Salary Components
        
        # Calculate totals
        total_grand_seconds = total_regular_seconds + total_overtime_seconds
        total_minutes_worked = int(total_grand_seconds / 60)
        
        overtime_hours = Decimal(total_overtime_seconds) / Decimal(3600)
        
        # Basic Rates
        basic_salary = 0
        daily_wage = 0
        per_minute_wage = 0
        
        if employee:
            basic_salary = employee.basic_salary
            daily_wage = basic_salary / 30 # Standard 30 days
            # Per Minute = Daily Wage / 8 hours (480 mins)
            # This is the standard rate derived from daily wage for an 8 hour shift
            # Rounding to 2 decimal places to match User's manual calculation (WYSIWYG)
            per_minute_wage = (daily_wage / Decimal(480)).quantize(Decimal("0.01"))

        # Earned Basic = Total Minutes * Minute Rate
        earned_basic = Decimal(total_minutes_worked) * per_minute_wage
        
        # OT Amount
        # Using the same minute rate for OT (1x) or specific Logic?
        # Code previously used: (daily_wage / 8) * overtime_hours
        # (daily_wage / 8) is exactly per_hour_wage. per_hour * hours = amount.
        # This matches calculated earned_basic logic if OT is paid at same rate.
        # However, typically Basic is for Regular hours and OT is separate.
        # The user requested "basic salary (earned)... must match total minutes worked * per minute charge".
        # This implies "Earned Basic" now effectively captures ALL work pay?
        # Wait, if we put ALL pay into Earned Basic, then Overtime Amount should be 0 or separate?
        # Usually:
        # Earned Basic = Regular Minutes * Rate
        # Overtime Pay = OT Minutes * Rate
        # Total = Earned Basic + OT Pay
        # "Total Minutes Worked" usually implies Regular + OT.
        # If user says "basic salary... match total minutes * charge", they might mean the SUM.
        # BUT the table has separate row for "Overtime Amount".
        # If I put everything in Basic, OT Amount row becomes redundant or double counting?
        # Let's check the previous code.
        # loops calculated total_regular_seconds and total_overtime_seconds.
        # User REQ: "basic salary (earned) ... match total minutes worked * per minute charge"
        # "Total Minutes Worked" in the summary table (line 328) is "total_minutes_worked" variable.
        # In my logic above, `total_minutes_worked` = reg + ot.
        # So I will set `earned_basic` = `total_minutes_worked` * `per_minute_wage`.
        # AND I will set `overtime_amount` to 0 ? Or is OT extra?
        # The UI shows "Basic Salary (Earned)" AND "Overtime Amount".
        # If I include OT in Basic, I should probably zero out OT Amount to avoid double pay, 
        # OR the user considers "Basic Salary" to be the line item for all time-based pay.
        # CHECK: The user said "basic salary... match total minutes...".
        # I will assume ONLY Basic Salary line changes its logic to cover everything, 
        # OR I separate them.
        # Given "match total minutes * per minute", I will make `earned_basic` cover it all.
        # But wait, there is a "Gross Salary" row = Basic + OT + Allowances.
        # If I put OT in Basic, Gross is fine.
        # BUT I should probably set Overtime Amount to 0 to be safe, OR:
        # Maybe "Total Minutes Worked" in user's mind is just Regular?
        # Looking at previous code: 
        # line 1068: 'total_minutes_worked': int(total_grand_seconds / 60) -> This INCLUDES OT.
        # So User really wants Basic Line = (Reg + OT) * Rate.
        # I will set Overtime Amount to 0 effectively, or I need to clarify?
        # "basic salary (earned) ... match total minutes worked * per minute charge"
        # I will do exactly that.
        
        overtime_amount = Decimal(0) 
        # IF I set this to 0, I should probably hide the row or just show 0.
        # OR does the user want:
        # Basic = Regular * Rate
        # OT = OT * Rate
        # And "Total Minutes" was just a reference?
        # The user said "basic salary ... must match total minutes worked * per minute charge".
        # This is a strong equality constraint. 
        # I will use the Exact Formula requested.
        # earned_basic = total_minutes_worked * per_minute_wage
        # overtime_amount = 0 (since it's included now)
        
        # However, to avoid confusion if they expect OT separately:
        # I will stick to the literal request.
        
        # WAIT! If I kill OT amount, I might break "Gross".
        # Gross = earned + allowances + ot.
        # If ot is 0, Gross = earned + allowances.
        # This seems correct for "Total Pay based on Time" being in one line.
        
        # Allowances
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

        gross_salary = earned_basic + total_allowances + overtime_amount # overtime_amount is 0
        
        # Deductions
        pf_eligible = basic_salary <= 15000
        esi_eligible = basic_salary <= 21000
        
        # PF: 12% of Earned Basic (which now includes OT? Standard is Basic+DA, excluding OT)
        # But with this custom logic, EarnedBasic is everything.
        # Let's assume PF applies to this new EarnedBasic.
        if pf_eligible:
            pf = earned_basic * Decimal('0.12')
        else:
            pf = Decimal('0.00')
            
        if esi_eligible:
             esi = gross_salary * Decimal('0.0075')
        else:
            esi = Decimal('0.00')
            
        if pf_eligible:
            employer_pf = earned_basic * Decimal('0.12')
        else:
            employer_pf = Decimal('0.00')
            
        if esi_eligible:
             employer_esi = earned_basic * Decimal('0.0325') # Note: using earned_basic not gross for employer share in this codebase previously?
             # Previous code: employer_esi = salary_from_days * Decimal('0.0325'). salary_from_days was "earned basic".
             # So yes, use earned_basic.
        else:
            employer_esi = Decimal('0.00')

        # Salary Advance
        advances = SalaryAdvance.objects.filter(employee=employee, date__range=[start_date, end_date])
        total_advance = advances.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')

        total_deductions = pf + esi + total_advance
        salary_payable = gross_salary - total_deductions
        
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
        
        summary_data = {
            'employee_name': employee.full_name if employee else "All Employees",
            'month': start_date.strftime("%B %Y"),
            'total_working_days': total_working_days,
            'total_present_days': present_days_count,
            'total_absent_days': absent_days_count,
            'total_working_hours': format_seconds(total_regular_seconds),
            'total_overtime_hours': format_seconds(total_overtime_seconds),
            'total_minutes_worked': total_minutes_worked,
            'total_gross_hours': format_seconds(total_grand_seconds), # NEW field
            
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
             'leave_cut_days': absent_days_count,
             'leave_cut_amount': basic_salary - earned_basic, # approx
             'total_unpaid_leaves': unpaid_leaves_count,
             
             'attendance_list': full_attendance_list
        }

        if action == 'download_pdf':
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="salary_slip_{employee.full_name}_{start_date.strftime("%B_%Y")}.pdf"'
            
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            p = canvas.Canvas(response, pagesize=letter)
            p.setFont("Helvetica-Bold", 16)
            p.drawString(100, 750, f"Salary Slip - {summary_data['month']}")
            
            p.setFont("Helvetica", 12)
            p.drawString(100, 720, f"Employee Name: {summary_data['employee_name']}")
            p.drawString(100, 700, f"Total Working Days: {summary_data['total_working_days']}")
            p.drawString(100, 680, f"Present Days: {summary_data['total_present_days']}")

            p.drawString(100, 660, f"Absent Days: {summary_data['total_absent_days']}")
            p.drawString(100, 640, f"Total Working Hours: {summary_data['total_working_hours']}")
            p.drawString(100, 620, f"Total Overtime Hours: {summary_data['total_overtime_hours']}")
            
            y = 590
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, y, "Earnings:")
            y -= 25
            p.setFont("Helvetica", 12)
            p.drawString(120, y, f"Basic Salary (Earned): {summary_data['earned_basic']:.2f}")
            y -= 20
            
            # Allowances
            for allowance in summary_data['allowance_list']:
                p.drawString(120, y, f"{allowance['name']}: {allowance['amount']:.2f}")
                y -= 20

            y -= 5
            p.line(120, y+15, 300, y+15) # Separator
            p.setFont("Helvetica-Bold", 12)
            p.drawString(120, y, f"Gross Salary: {summary_data['gross_salary']:.2f}")

            y -= 40
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, y, "Deductions:")
            y -= 25
            p.setFont("Helvetica", 12)
            p.drawString(120, y, f"PF (12%): {summary_data['pf']:.2f}")
            y -= 20
            p.drawString(120, y, f"ESI (0.75%): {summary_data['esi']:.2f}")
            y -= 20
            
            y -= 5
            p.line(120, y+15, 300, y+15) # Separator
            p.setFont("Helvetica-Bold", 12)
            p.drawString(120, y, f"Total Deductions: {summary_data['total_deductions']:.2f}")
            
            y -= 40
            p.setFont("Helvetica-Bold", 14)
            p.drawString(100, y, f"Net Salary Payable: {summary_data['salary_payable']:.2f}")

            p.showPage()
            p.save()
            return response

    context = {
        'form': form,
        'summary_data': summary_data,
    }
    return render(request, 'core/summary.html', context)

@login_required
def export_employees_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="employees.csv"'

    writer = csv.writer(response)
    writer.writerow(['Employee Code', 'Full Name', 'Department', 'Designation', 'Joining Date', 'Mobile'])

    employees = Employee.objects.all()
    for emp in employees:
        writer.writerow([
            emp.employee_code,
            emp.full_name,
            emp.department.name if emp.department else 'N/A',
            emp.designation.name if emp.designation else 'N/A',
            emp.joining_date,
            emp.contact_number,
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
            
            return JsonResponse({'status': 'success', 'message': f"Successfully processed {results['processed_count']} records from {results['devices_connected']} devices. {processed_absent} marked absent."}, status=200)
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
    ).order_by('-date')
    
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
        'years': range(current_date.year - 2, current_date.year + 3)
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
    
    employees = Employee.objects.all()
    report_data = []
    
    for emp in employees:
        present_days = Attendance.objects.filter(employee=emp, date__range=[start_date, end_date]).count()
        leaves = Leave.objects.filter(employee=emp, start_date__lte=end_date, end_date__gte=start_date, status='Approved')
        
        # Calculate Leave Days excluding Holidays
        unpaid_leave_days = 0
        total_leave_days = 0 
        for leave in leaves:
            l_start = max(leave.start_date, start_date)
            l_end = min(leave.end_date, end_date)
            
            # Iterate through each day of the leave
            curr_date = l_start
            while curr_date <= l_end:
                # Count as leave matching Summary View logic (Leave > Holiday priority)
                # Summary view counts it as Unpaid Leave even if it is a holiday
                total_leave_days += 1
                if leave.leave_type == 'Unpaid':
                    unpaid_leave_days += 1
                curr_date += datetime.timedelta(days=1)
        
        basic = emp.basic_salary
        if not basic: basic = Decimal(0)
        # Standardize on Basic / 30
        daily_rate = basic / Decimal(30)
        
        # Overtime & Presence Calculation
        att_records = Attendance.objects.filter(employee=emp, date__range=[start_date, end_date])
        # Total Seconds Calculation - Aligned with Summary View Logic (Lines 930-1060)
        total_regular_seconds = 0
        total_overtime_seconds = 0
        
        # Pre-fetch attendance map for O(1) lookup
        att_map = {}
        for att in att_records:
            att_map[att.date] = att

        # Pre-fetch leave map
        leave_map = {}
        # Fetch leaves again to be sure (or use existing 'leaves' qs)
        for leaves_req in leaves:
             # Iterate days
             c = max(leaves_req.start_date, start_date)
             e = min(leaves_req.end_date, end_date)
             current = c
             while current <= e:
                 leave_map[current] = leaves_req.leave_type
                 current += datetime.timedelta(days=1)

        # Iterate all days in month
        current_iter_date = start_date
        present_on_working_days = 0
        absent_days_count = 0
        
        while current_iter_date <= end_date:
            day_record = att_map.get(current_iter_date)
            # Replicate Summary Logic: If a record exists (even empty/0-duration), it counts as "presence attempt" 
            # and suppresses automatic Holiday/Leave 8h credit.
            has_record = day_record is not None
            
            if day_record and day_record.check_in_time and day_record.check_out_time:
                 # Check valid duration
                 check_in = datetime.datetime.combine(current_iter_date, day_record.check_in_time)
                 check_out = datetime.datetime.combine(current_iter_date, day_record.check_out_time)
                 if check_out < check_in: check_out += datetime.timedelta(days=1)
                 
                 raw_seconds = (check_out - check_in).total_seconds()
                 if raw_seconds > 0:
                     # Valid Work detected
                     
                     # Count for Absent Deduction (Present on Working Day)
                     if current_iter_date not in holiday_set:
                         present_on_working_days += 1
                     
                     deduction = 3600
                     if day_record.no_break: deduction = 0
                     
                     seconds = raw_seconds - deduction
                     if seconds < 0: seconds = 0
                     
                     if current_iter_date in holiday_set:
                         # Worked on Holiday
                         # Regular = 8h Entitlement, Overtime = Worked Duration
                         total_regular_seconds += 28800
                         total_overtime_seconds += seconds
                     else:
                         # Regular Day
                         if seconds > 28800:
                             total_regular_seconds += 28800
                             total_overtime_seconds += (seconds - 28800)
                         else:
                             total_regular_seconds += seconds

            # Only apply automatic credits if NO record exists
            if not has_record:
                 # Check Leave
                 if current_iter_date in leave_map:
                     l_type = leave_map[current_iter_date]
                     if l_type == 'Paid':
                         total_regular_seconds += 28800
                         
                 # Check Holiday (Only if not Leave)
                 elif current_iter_date in holiday_set:
                     total_regular_seconds += 28800
                 
                 else:
                     # No Record, No Leave, No Holiday -> Absent
                     absent_days_count += 1
            
            current_iter_date += datetime.timedelta(days=1)

        # Minute-Based Calculation
        total_grand_seconds = total_regular_seconds + total_overtime_seconds
        total_minutes_worked = int(total_grand_seconds / 60)
        
        # OT Hours Display (HH:MM)
        ot_h = int(total_overtime_seconds // 3600)
        ot_m = int((total_overtime_seconds % 3600) // 60)
        overtime_hours_str = f"{ot_h:02d}:{ot_m:02d}"
        
        # OT Amount: Daily / 8 (Net) * Hours
        # We already calculated ot_amount correctly based on minutes above using rate
        # ot_amount = Decimal(ot_minutes) * per_minute_wage
        # Per Minute Wage (Rounded to 2 decimals)
        per_minute_wage = Decimal(0)
        daily_rate = basic / Decimal(30)
        if basic > 0:
            per_minute_wage = (daily_rate / Decimal(480)).quantize(Decimal("0.01"))
        
        # Calculate OT Minutes for Amount
        ot_minutes = int(total_overtime_seconds / 60)
        
        # Total Earned (Reg + OT) - Source of Truth for Gross
        total_earned = Decimal(total_minutes_worked) * per_minute_wage
        
        # OT Amount
        ot_amount = Decimal(ot_minutes) * per_minute_wage
        
        # Earned Basic (Regular Only)
        earned_basic_regular = total_earned - ot_amount
        
        total_allowances = sum([ea.amount for ea in emp.employeeallowance_set.all()])
        
        # Gross = Total Earned + Allowances
        gross_salary = total_earned + total_allowances
        
        pf = Decimal(0)
        esi = Decimal(0)
        
        # PF is likely based on Total Basic Earned (including OT in this specific payroll logic based on user request)
        if basic <= 15000:
             pf = total_earned * Decimal('0.12')
        
        if basic <= 21000:
             esi = gross_salary * Decimal('0.0075')

        advances_total = SalaryAdvance.objects.filter(employee=emp, date__range=[start_date, end_date]).aggregate(sum=Sum('amount'))['sum'] or 0
        
        # Total Deductions
        total_deductions = pf + esi + advances_total
        
        # Net Salary
        net_salary = gross_salary - total_deductions
        
        # Leaves & Leave Cut Amount
        # Leave Cut should reflect loss of Regular Pay
        leave_cut_amount = basic - earned_basic_regular
        if leave_cut_amount < 0: leave_cut_amount = 0
        
        # Display purposes
        working_hours_decimal = total_regular_seconds / 3600.0
        wh_hours = int(working_hours_decimal)
        wh_minutes = int((working_hours_decimal - wh_hours) * 60)
        total_working_hours_str = f"{wh_hours:02d}:{wh_minutes:02d}"
        
        report_data.append({
            'emp_id': emp.pk,
            'code': emp.employee_code,
            'name': emp.full_name,
            'doj': emp.joining_date,
            'basic': basic,
            'allowances': total_allowances,
            'overtime_hours': overtime_hours_str,
            'overtime_amount': round(ot_amount, 2),
            'salary_advance': advances_total,
            'esic': round(esi, 2),
            'pf': round(pf, 2),
            'leaves': unpaid_leave_days,
            'leave_cut_amount': round(leave_cut_amount, 2),
            'working_hours': total_working_hours_str,
            'total_salary': round(gross_salary, 2),
            'net_salary': round(net_salary, 2)
        })


    context = {
        'report_data': report_data,
        'selected_month': selected_month,
        'selected_year': selected_year,
        'months': list(enumerate(calendar.month_name))[1:],
        'years': range(current_date.year - 2, current_date.year + 3)
    }
    return render(request, 'core/monthly_salary_report.html', context)

@hr_required
def toggle_no_break(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)
    attendance.no_break = not attendance.no_break
    attendance.save()
    
    # Redirect back to previous page
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('summary')