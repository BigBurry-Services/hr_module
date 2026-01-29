
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
                defaults = {}
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
                    attendance.save()
                    
                messages.success(request, f"Updated Attendance for {employee.full_name}")
                
            else:
                 # Nothing provided? logic hole?
                 # Maybe user cleared everything?
                 pass

        except Exception as e:
            messages.error(request, f"Error updating: {e}")
            
        return redirect(f"{reverse('attendance_mark')}?date={date_str}")
    return redirect('attendance_mark')
