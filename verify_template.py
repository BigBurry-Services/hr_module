
import os
import django
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from django.test import RequestFactory
from core.views import summary

def test_template_render():
    print("Testing template rendering...")
    try:
        # Mock Context Data
        context = {
            'summary_data': {
                'employee_name': 'Test User',
                'month': 'December 2025',
                'earned_basic': 5000,
                'da': 1000,
                'hra': 500,
                'allowance_list': [{'name': 'Test Allow', 'amount': 200}],
                'gross_salary': 6700,
                'pf': 720,
                'esi': 0,
                'total_deductions': 720,
                'salary_payable': 5980,
                'total_working_days': 30,
                'total_present_days': 30,
                'total_absent_days': 0,
                'attendance_list': []
            },
            'form': None # Mock form if needed, but 'as_p' might fail if None. 
            # Ideally we should use the actual view or render_to_string with request.
        }
        
        # We can just try to compile the template first to check for syntax errors
        from django.template.loader import get_template
        t = get_template('core/summary.html')
        print("Template compiled successfully.")
        
    except Exception as e:
        print(f"Template Error: {e}")

if __name__ == '__main__':
    test_template_render()
