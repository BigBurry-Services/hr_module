import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.models import Employee, SalaryAdvance
from django.db.models import Q

def verify_search_logic():
    # Assume data exists or just test the query logic validity
    print("Verifying Search Query Logic...")
    
    search_query = "Test"
    qs = SalaryAdvance.objects.all()
    filtered_qs = qs.filter(
        Q(employee__full_name__icontains=search_query) |
        Q(employee__employee_code__icontains=search_query)
    )
    print("Query Construction Successful.")
    
if __name__ == '__main__':
    verify_search_logic()
