import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()
from core.models import LeaveType
for lt in LeaveType.objects.all():
    print(f"ID: {lt.id}, Name: '{lt.name}'")
