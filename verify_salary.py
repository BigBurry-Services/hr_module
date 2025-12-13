
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee, Allowance, EmployeeAllowance
from core.views import summary
from django.test import RequestFactory, Client
import datetime

# Setup Test Data
def test_salary_logic():
    print("Setting up test data...")
    # 1. Create Employee
    emp, created = Employee.objects.get_or_create(
        employee_code="TEST001",
        defaults={
            'full_name': "Test User",
            'basic_salary': 10000.00,
            'da': 2000.00,
            'hra': 1000.00
        }
    )
    if not created:
        emp.basic_salary = 10000.00
        emp.da = 2000.00
        emp.hra = 1000.00
        emp.save()

    print(f"Employee: Basic={emp.basic_salary}, DA={emp.da}, HRA={emp.hra}")
    
    # 2. Logic Check
    # Scenario: Full month present (30 days)
    # Expected:
    # Earned Basic = 10000
    # Gross = 10000 + 2000 + 1000 = 13000
    # PF = 12% of (10000 + 2000) = 1440
    # ESI = 0.75% of 13000 (since < 21000) = 97.5
    # Net = 13000 - 1440 - 97.5 = 11462.5
    
    daily_wage = float(emp.basic_salary) / 30
    present_days = 30
    salary_from_days = daily_wage * present_days
    
    pf_base = salary_from_days + float(emp.da)
    pf = pf_base * 0.12
    
    gross = salary_from_days + float(emp.da) + float(emp.hra)
    esi = 0
    if gross <= 21000:
        esi = gross * 0.0075
        
    net = gross - (pf + esi)
    
    print("\nExpected Calculations (Manual):")
    print(f"Gross: {gross}")
    print(f"PF: {pf}")
    print(f"ESI: {esi}")
    print(f"Net: {net}")
    
    print("\nNote: This script simulates the logic used in views.py. To fully test views, we'd need to mock requests/attendance.")
    
if __name__ == '__main__':
    test_salary_logic()
