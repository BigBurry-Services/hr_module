
import os
import django
import sys

# Set up Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee

codes_to_check = ['30', '24', '36', 'A30', 'A24', 'A36', '5']

print("Checking for employees with specific codes:")
for code in codes_to_check:
    try:
        emp = Employee.objects.get(employee_code=code)
        print(f"FOUND: Code '{code}' -> {emp.full_name} (ID: {emp.id})")
    except Employee.DoesNotExist:
        print(f"NOT FOUND: Code '{code}'")

print("\nListing all employees with numeric-only codes vs alphanumeric:")
all_emps = Employee.objects.all()
for emp in all_emps:
    print(f"Code: '{emp.employee_code}' - Name: {emp.full_name}")
