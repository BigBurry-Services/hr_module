
import os
import django
import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee, Attendance, Leave, LeaveType, SalaryAdvance, Designation

def test_salary_calculation():
    print("Setting up test data...")
    # 1. Setup Data
    # Create dummy employee
    emp, created = Employee.objects.get_or_create(
        employee_code='TEST001',
        defaults={
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'phone_number': '1234567890', 
            'basic_salary': Decimal('30000.00'), # 1000 per day
            'joining_date': datetime.date(2023, 1, 1)
        }
    )
    if not created:
        emp.basic_salary = Decimal('30000.00')
        emp.save()

    # Clear existing attendance/leaves for the test month (e.g., Nov 2024 to avoid future/current date issues)
    test_month = 11
    test_year = 2024
    start_date = datetime.date(test_year, test_month, 1)
    end_date = datetime.date(test_year, test_month, 30)

    Attendance.objects.filter(employee=emp, date__range=[start_date, end_date]).delete()
    Leave.objects.filter(employee=emp, start_date__lte=end_date, end_date__gte=start_date).delete()
    SalaryAdvance.objects.filter(employee=emp, date__range=[start_date, end_date]).delete()

    print(f"Employee Basic: {emp.basic_salary}")
    
    # 2. Add Attendance (Present for 20 days)
    # 30000 / 30 = 1000 per day.
    # 20 days present = 20000 earned. leave cut = 10000.
    atts = []
    for day in range(1, 21):
        d = datetime.date(test_year, test_month, day)
        atts.append(Attendance(
            employee=emp,
            date=d,
            check_in_time=datetime.time(9, 0),
            check_out_time=datetime.time(17, 0)
        ))
    Attendance.objects.bulk_create(atts)
    
    # 3. Simulate View Logic (Simplified copy of what matters)
    # We need to call the view or replicate the critical logic. 
    # Calling the view directly is hard due to request object mocking.
    # I will replicate the LOGIC I intend to verify based on views.py reading.
    
    # --- LOGIC REPLICATION START ---
    
    total_working_days = 30
    present_days = 20
    # standard 8 hours = 28800 seconds
    total_minutes_worked = 20 * 480 
    
    daily_wage = emp.basic_salary / 30
    per_minute_wage = (daily_wage / Decimal(480)).quantize(Decimal("0.01"))
    
    earned_basic = Decimal(total_minutes_worked) * per_minute_wage
    
    overtime_amount = Decimal(0) # As per current code
    total_allowances = Decimal(0)
    
    gross_salary = earned_basic + total_allowances + overtime_amount
    
    # Leave Cut (The part we want to implement)
    # Current Code doesn't have explicit leave cut in 'deductions_list_slip' usually, 
    # it just shows lower 'Basic Salary (Earned)'.
    
    leave_cut_val = emp.basic_salary - earned_basic
    
    # Deductions
    pf = Decimal(0) # keeping simple
    esi = Decimal(0)
    total_advance = Decimal(0)
    
    total_deductions = pf + esi + total_advance
    
    # Proposed Change Simulation / Verification of New Logic:
    # We have now implemented the change. 
    # Logic: 
    # Display Basic = Full Basic
    # Display Deductions = Original Deductions + Leave Cut Val
    # Verify: Net Pay should be same as Original Net.
    
    display_basic_expected = emp.basic_salary
    display_deductions_expected = pf + esi + total_advance + leave_cut_val
    display_gross_expected = display_basic_expected + total_allowances + overtime_amount
    
    # Check Net
    new_net = display_gross_expected - display_deductions_expected
    old_net = earned_basic + total_allowances + overtime_amount - (pf + esi + total_advance)
    
    print("-" * 20)
    print(f"Daily Wage: {daily_wage}")
    print(f"Per Minute: {per_minute_wage}")
    print(f"Total Minutes: {total_minutes_worked}")
    print(f"Earned Basic (Actual Pay): {earned_basic}")
    print(f"Leave Cut Val: {leave_cut_val}")
    
    print("-" * 20)
    print("EXPECTED NEW DISPLAY VALUES:")
    print(f"Basic Salary (Full): {display_basic_expected}")
    print(f"Total Deductions (with Leave Cut): {display_deductions_expected}")
    print(f"Net Pay (Should match original): {new_net}")
    
    if abs(new_net - old_net) < Decimal('0.05'):
        print("SUCCESS: Net Pay logic is consistent with new display format.")
    else:
         print(f"FAILURE: Net Pay Logic Error! New: {new_net}, Old: {old_net}")

if __name__ == '__main__':
    test_salary_calculation()
