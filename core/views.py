from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
import datetime
import calendar
import csv
from .models import Employee, Attendance, HRProfile, Department, Designation, Allowance, AttendanceDevice, EmployeeAllowance
from django.contrib.auth.models import User
from django.db import transaction
from .forms import EmployeeForm, AttendanceForm, SalarySummaryForm, RegistrationForm, DepartmentForm, DesignationForm, AllowanceForm, AttendanceDeviceForm, EmployeeAllowanceFormSet

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
    # Check dependencies
    related_employees = Employee.objects.filter(department=department)
    related_count = related_employees.count()

    if request.method == 'POST':
        if related_count > 0:
            return render(request, 'core/department_confirm_delete.html', {
                'department': department,
                'related_employees': related_employees,
                'related_count': related_count,
                'error': "Cannot delete department with assigned employees."
            })
        department.delete()
        return redirect('department_list')
    return render(request, 'core/department_confirm_delete.html', {
        'department': department,
        'related_employees': related_employees,
        'related_count': related_count
    })

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
    # Check dependencies
    related_employees = Employee.objects.filter(designation=designation)
    related_count = related_employees.count()

    if request.method == 'POST':
        if related_count > 0:
            return render(request, 'core/designation_confirm_delete.html', {
                'designation': designation,
                'related_employees': related_employees,
                'related_count': related_count,
                'error': "Cannot delete designation with assigned employees."
            })
        designation.delete()
        return redirect('designation_list')
    return render(request, 'core/designation_confirm_delete.html', {
        'designation': designation,
        'related_employees': related_employees,
        'related_count': related_count
    })

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
    
    return render(request, 'core/employee_list.html', {
        'employees': employees,
        'search_query': search_query
    })

@login_required
def employee_add(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        formset = EmployeeAllowanceFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    employee = form.save()
                    formset.instance = employee
                    formset.save()
                    return redirect('employee_list')
            except Exception as e:
                # Handle errors (could add message to user)
                pass
    else:
        form = EmployeeForm()
        formset = EmployeeAllowanceFormSet()
    return render(request, 'core/employee_form.html', {'form': form, 'formset': formset})

@login_required
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    return render(request, 'core/employee_detail.html', {'employee': employee})

@login_required
def employee_edit(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        formset = EmployeeAllowanceFormSet(request.POST, instance=employee)
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    formset.save()
                    return redirect('employee_list')
            except Exception as e:
                pass
    else:
        form = EmployeeForm(instance=employee)
        formset = EmployeeAllowanceFormSet(instance=employee)
    return render(request, 'core/employee_form.html', {'form': form, 'formset': formset})

@login_required
def employee_delete(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    if request.method == 'POST':
        employee.delete()
        return redirect('employee_list')
    return render(request, 'core/employee_confirm_delete.html', {'employee': employee})

@login_required
def attendance_mark(request):
    departments = Department.objects.all()
    
    # Filter variables
    selected_dept_id = request.GET.get('department')
    selected_date_str = request.GET.get('date', datetime.date.today().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = datetime.date.today()

    # Get Employees based on filter
    employees = Employee.objects.all()
    if selected_dept_id:
        employees = employees.filter(department_id=selected_dept_id)

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
        
        # Refresh attendance map after changes
        existing_attendance = Attendance.objects.filter(date=selected_date)
        attendance_map = {att.employee_id: att for att in existing_attendance}

    context = {
        'departments': departments,
        'employees': employees,
        'attendance_map': attendance_map,
        'selected_dept_id': int(selected_dept_id) if selected_dept_id else None,
        'selected_date': selected_date_str,
        'error_message': error_message,
        'success_message': success_message,
    }
    return render(request, 'core/attendance_mark.html', context)

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
    """
    Redirects to the device list since management is now handled there.
    Kept for backward compatibility or future aggregation.
    """
    return redirect('device_list')

@login_required
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


@login_required
def summary(request):
    form = SalarySummaryForm(request.POST or None)
    summary_data = None

    if request.method == 'POST' and form.is_valid():
        month = int(form.cleaned_data['month'])
        employee = form.cleaned_data['employee']
        action = request.POST.get('action', 'generate')
        
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

        # Salary Calculation
        daily_wage = 0
        basic_salary = 0
        da = 0
        hra = 0
        if employee:
            basic_salary = employee.basic_salary
            da = employee.da
            hra = employee.hra
            daily_wage = basic_salary / 30 # Assuming 30 days
        
        salary_from_days = daily_wage * present_days
        
        # Add Allowances
        total_allowances = 0
        allowance_list = []
        if employee:
            # Iterate over the through-model to get specific amounts
            # Use select_related to avoid N+1 queries
            emp_allowances = employee.employeeallowance_set.select_related('allowance').all()
            for emp_allowance in emp_allowances:
                amount = emp_allowance.amount
                total_allowances += amount
                allowance_list.append({
                    'name': emp_allowance.allowance.name,
                    'amount': amount
                })
        
        salary_payable = salary_from_days + total_allowances + da + hra

        summary_data.update({
             'basic_salary': basic_salary,
             'da': da,
             'hra': hra,
             'total_allowances': total_allowances,
             'allowance_list': allowance_list,
             'salary_payable': salary_payable,
             'daily_wage': daily_wage,
             'attendance_list': attendance_records.order_by('date')
        })

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
            
            p.drawString(100, 630, "Earnings:")
            p.drawString(120, 610, f"Basic Salary (Pro-rated): {salary_from_days:.2f} (Full: {basic_salary})")
            p.drawString(120, 590, f"DA: {da}")
            p.drawString(120, 570, f"HRA: {hra}")
            p.drawString(120, 550, f"Total Allowances: {total_allowances:.2f}")
            
            p.setFont("Helvetica-Bold", 12)
            p.drawString(100, 520, f"Net Salary Payable: {salary_payable:.2f}")

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