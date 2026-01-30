import os
import django
from django.db.models import Count

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Attendance

def check_duplicates():
    duplicates = Attendance.objects.values('employee', 'date').annotate(count=Count('id')).filter(count__gt=1)
    if duplicates.exists():
        print("Duplicates found:")
        for dup in duplicates:
            print(f"Employee {dup['employee']} on {dup['date']}: {dup['count']} records")
    else:
        print("No duplicates found in Attendance.")

if __name__ == '__main__':
    check_duplicates()
