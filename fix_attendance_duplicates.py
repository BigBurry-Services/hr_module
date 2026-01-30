import os
import django
from django.db.models import Count, Max

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Attendance

def clean_duplicates():
    # Identify duplicates by grouping by employee and date
    duplicates = Attendance.objects.values('employee', 'date').annotate(count=Count('id')).filter(count__gt=1)
    
    deleted_count = 0
    
    print(f"Found {duplicates.count()} sets of duplicates.")
    
    for dup in duplicates:
        employee_id = dup['employee']
        date = dup['date']
        
        # Get all records for this employee and date
        records = Attendance.objects.filter(employee_id=employee_id, date=date).order_by('-id')
        
        # Keep the first one (latest ID), delete the rest
        # You might want to be smarter (e.g. keep the one with check-out), but for now latest is likely best from sync
        to_keep = records.first()
        to_delete = records.exclude(id=to_keep.id)
        
        print(f"Keeping record {to_keep.id} for Employee {employee_id} on {date}. Deleting {to_delete.count()} duplicates.")
        
        count, _ = to_delete.delete()
        deleted_count += count

    print(f"Total duplicate records deleted: {deleted_count}")

if __name__ == '__main__':
    clean_duplicates()
