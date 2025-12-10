import os
import django
import sys
import datetime
from django.test import RequestFactory

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

from core.views import summary
from core.models import Employee, Attendance, Allowance, EmployeeAllowance

def verify_summary():
    # Setup Data
    print("Setting up test data...")
    emp = Employee.objects.first()
    if not emp:
        print("No employee found. Cannot proceed.")
        return

    # Ensure some attendance for current month
    today = datetime.date.today()
    Attendance.objects.create(employee=emp, date=today, check_in_time="09:00:00")
    
    # Ensure some allowance
    allowance, _ = Allowance.objects.get_or_create(name="Test Allowance")
    EmployeeAllowance.objects.update_or_create(employee=emp, allowance=allowance, defaults={'amount': 1000})

    # Create Request
    factory = RequestFactory()
    data = {'month': today.month, 'employee': emp.id, 'action': 'generate'}
    request = factory.post('/core/summary/', data)
    request.user = emp.user if hasattr(emp, 'user') else None # Mock user if needed, but view uses decorators

    # We need to bypass login_required for direct function call or mock request.user
    # Since we imported the view function directly, the decorator wraps it.
    # To test logic inside, it's easier to mock the request user as authenticated.
    from django.contrib.auth.models import User
    user = User.objects.first() or User.objects.create_user('testuser', 'test@example.com', 'password')
    request.user = user

    print("Calling summary view...")
    response = summary(request)
    
    if response.status_code == 200:
        print("View returned 200 OK.")
        # Context is not directly accessible from response unless we use test client.
        # However, we can inspect the rendered content or use a trick.
        # But `render` returns HttpResponse. 
        # Let's verify by printing what we expect logic to have done
        # Ideally, we should have extracted logic to a helper function.
        # Since we modified the view, let's just check if it runs without error 
        # and maybe print the content to see if new fields are there.
        content = response.content.decode('utf-8')
        
        required_strings = [
            "Attendance Statistics",
            "Salary Details",
            "Basic Salary (Monthly):",
            "Net Salary Payable",
            "Attendance History",
            "Test Allowance"
        ]
        
        missing = [s for s in required_strings if s not in content]
        
        if missing:
            print(f"FAILURE: Missing strings in output: {missing}")
        else:
            print("SUCCESS: All new sections found in rendered HTML.")
            
    else:
        print(f"FAILURE: View returned {response.status_code}")

if __name__ == "__main__":
    verify_summary()
