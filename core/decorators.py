from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def admin_required(function=None):
    """
    Decorator for views that checks that the user is logged in and is an Admin (Role 0).
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_superuser or (hasattr(u, 'hrprofile') and u.hrprofile.role == 0)),
        login_url='login',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def hr_required(function=None):
    """
    Decorator for views that checks that the user is logged in and is HR (Role 1) or Admin (Role 0).
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_superuser or (hasattr(u, 'hrprofile') and (u.hrprofile.role == 0 or u.hrprofile.role == 1))),
        login_url='login',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
