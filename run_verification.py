import os
import django
import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee, Attendance, Holiday, Leave, SalaryAdvance

def verify():
    print("Verifying Salary and Leaves...")

    # Teardown previous test data
    Employee.objects.filter(employee_code='TEST001').delete()
    # Holiday.objects.all().delete() # commented out to avoid wiping user data if any, though local likely ok
    
    # Setup
    emp = Employee.objects.create(
        employee_code='TEST001',
        full_name='Test Employee',
        basic_salary=30000, # 30k
        joining_date=datetime.date(2025, 1, 1)
    )
    
    # Create Holiday
    # Add holidays for Jan 2025 if not exist
    h_dates = [datetime.date(2025, 1, 5), datetime.date(2025, 1, 12), datetime.date(2025, 1, 19), datetime.date(2025, 1, 26)]
    for d in h_dates:
        Holiday.objects.get_or_create(date=d, defaults={'description': "Sunday"})
    
    # Count holidays in Jan 2025
    jan_start = datetime.date(2025, 1, 1)
    jan_end = datetime.date(2025, 1, 31)
    holidays_count = Holiday.objects.filter(date__range=[jan_start, jan_end]).count()
    print(f"Holidays in Jan 2025: {holidays_count}")
    
    # Working Days = 31 - holidays_count
    working_days = 31 - holidays_count
    daily_rate = Decimal(30000) / Decimal(working_days)
    print(f"Working Days: {working_days}")
    print(f"Daily Rate: {daily_rate:.2f}")
    
    # Add Attendance
    # Present for 5 days
    for i in range(1, 6):
        Attendance.objects.create(
            employee=emp,
            date=datetime.date(2025, 1, i),
            check_in_time=datetime.time(9, 0),
            check_out_time=datetime.time(18, 0)
        )
        
    # Add Leave (Unpaid)
    # 2 days unpaid
    Leave.objects.create(
        employee=emp,
        start_date=datetime.date(2025, 1, 7),
        end_date=datetime.date(2025, 1, 8),
        leave_type='Unpaid',
        status='Approved',
        reason='Test'
    )
    
    # Add Leave (Paid)
    # 1 day paid
    Leave.objects.create(
        employee=emp,
        start_date=datetime.date(2025, 1, 9),
        end_date=datetime.date(2025, 1, 9),
        leave_type='Paid',
        status='Approved',
        reason='Test'
    )
    
    # Simulating View Logic
    present_days = Attendance.objects.filter(employee=emp, date__range=[jan_start, jan_end]).count()
    leaves = Leave.objects.filter(employee=emp, start_date__lte=jan_end, end_date__gte=jan_start, status='Approved')
    
    unpaid_leave_days = 0
    total_leave_days = 0 
    for leave in leaves:
        l_start = max(leave.start_date, jan_start)
        l_end = min(leave.end_date, jan_end)
        days = (l_end - l_start).days + 1
        if days > 0:
            total_leave_days += days
            if leave.leave_type == 'Unpaid':
                unpaid_leave_days += days
                
    absent_days = working_days - present_days - total_leave_days
    if absent_days < 0: absent_days = 0
    
    leave_cut = unpaid_leave_days * daily_rate
    absent_deduction = absent_days * daily_rate
    
    print(f"Present: {present_days}, Leaves: {total_leave_days} (Unpaid: {unpaid_leave_days}), Absent: {absent_days}")
    print(f"Leave Cut: {leave_cut:.2f}")
    print(f"Absent Deduction: {absent_deduction:.2f}")
    
    net_salary = Decimal(30000) - leave_cut - absent_deduction
    print(f"Net Salary: {net_salary:.2f}")

    # Cleanup
    # emp.delete() # Keep it to inspect manually if needed? Nah delete.
    emp.delete()
    print("Verification Script Finished.")

if __name__ == '__main__':
    verify()
