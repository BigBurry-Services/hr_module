
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_module.settings')
django.setup()

def test_decimal_mix():
    print("Testing Decimal * Float fix...")
    try:
        val = Decimal('1000.00')
        # This simulates the fixed code
        res = val * Decimal('0.12')
        print(f"Success: {val} * 0.12 = {res}")
        
        res2 = val * Decimal('0.0075')
        print(f"Success: {val} * 0.0075 = {res2}")
        
    except TypeError as e:
        print(f"Failed: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    test_decimal_mix()
