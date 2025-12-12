
import os
import django
from unittest.mock import MagicMock, patch
from datetime import datetime, time, date

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hr_module.settings")
django.setup()

from core.utils import DeviceSyncService
from core.models import Employee, Attendance

def test_sync_logic():
    print("Testing Device Sync Logic...")
    
    # Mock Data based on user input
    # {'user_id': '5', 'timestamp': '2025-12-08 19:09:56', 'status': 15} -> Out?
    # {'user_id': '263', 'timestamp': '2025-12-08 19:17:22', 'status': 15}
    # {'user_id': '155', 'timestamp': '2025-12-08 19:17:28', 'status': 1} -> In?
    
    # Let's create a mock employee
    Employee.objects.filter(employee_code='5').delete()
    emp = Employee.objects.create(employee_code='5', first_name='Test', last_name='User', basic_salary=1000)
    
    # Mock Punches
    # Scenario 1: Mixed Status
    # In at 10:00 (Status 1), Out at 18:00 (Status 15)
    punches_mixed = [
        {'time': time(10, 0, 0), 'status': 1},
        {'time': time(18, 0, 0), 'status': 15}
    ]
    
    service = DeviceSyncService()
    
    target_date = date(2025, 12, 12)
    user_punches = {'5': punches_mixed}
    
    print("Scenario 1: Explicit In (1) and Out (15)")
    service.process_punches(user_punches, target_date)
    
    att = Attendance.objects.get(employee=emp, date=target_date)
    print(f"Result: In={att.check_in_time}, Out={att.check_out_time}")
    
    assert att.check_in_time == time(10, 0, 0)
    assert att.check_out_time == time(18, 0, 0)
    print("PASS")
    
    # Scenario 2: Multiple punches, no explicit status (all likely 1 or unknown)
    # 09:00, 12:00, 13:00, 17:00. All status 1.
    # Should take First and Last.
    punches_ambiguous = [
        {'time': time(9, 0, 0), 'status': 1},
        {'time': time(12, 0, 0), 'status': 1},
        {'time': time(13, 0, 0), 'status': 1},
        {'time': time(17, 0, 0), 'status': 1},
    ]
    user_punches = {'5': punches_ambiguous}
    
    print("\nScenario 2: Ambiguous Status (All 1)")
    service.process_punches(user_punches, target_date) # Updates existing
    
    att.refresh_from_db()
    print(f"Result: In={att.check_in_time}, Out={att.check_out_time}")
    
    assert att.check_in_time == time(9, 0, 0)
    assert att.check_out_time == time(17, 0, 0)
    print("PASS")

    # Scenario 3: Single Punch
    # Only 09:30
    punches_single = [
        {'time': time(9, 30, 0), 'status': 1}
    ]
    user_punches = {'5': punches_single}
    
    print("\nScenario 3: Single Punch")
    service.process_punches(user_punches, target_date)
    
    att.refresh_from_db()
    print(f"Result: In={att.check_in_time}, Out={att.check_out_time}")
    
    assert att.check_in_time == time(9, 30, 0)
    assert att.check_out_time is None
    print("PASS")

    # Cleanup
    emp.delete()
    print("\nCleanup Done.")

if __name__ == "__main__":
    try:
        test_sync_logic()
        print("\nAll Tests Passed Successfully!")
    except Exception as e:
        print(f"\nTest Failed: {e}")
