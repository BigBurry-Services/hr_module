import os
import django
import sys

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee

print("Checking Employee string representation...")
emp = Employee.objects.first()
if emp:
    print(f"Employee found: {emp.full_name}")
    print(f"ID: {emp.employee_code}")
    print(f"String Representation: '{str(emp)}'")
    expected = f"{emp.full_name} ({emp.employee_code})"
    if str(emp) == expected:
        print("SUCCESS: String representation matches expected format.")
    else:
        print(f"FAILURE: Expected '{expected}', got '{str(emp)}'")
else:
    print("No employees found to test.")
