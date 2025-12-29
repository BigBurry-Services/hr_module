import os
import django
import datetime

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee

def verify_birthdays():
    today = datetime.date.today()
    print(f"Current Month: {today.strftime('%B')}")
    
    # Query used in view
    birthdays_this_month = Employee.objects.filter(
        date_of_birth__month=today.month
    ).exclude(date_of_birth__isnull=True).order_by('date_of_birth__day')
    
    print(f"Found {birthdays_this_month.count()} birthdays:")
    for emp in birthdays_this_month:
        print(f"- {emp.full_name}: {emp.date_of_birth} (Day: {emp.date_of_birth.day})")

if __name__ == '__main__':
    verify_birthdays()
