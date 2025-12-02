from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import HRProfile, Employee, Attendance, Department, Designation

# Define an inline admin descriptor for HRProfile model
# which acts a bit like a singleton
class HRProfileInline(admin.StackedInline):
    model = HRProfile
    can_delete = False
    verbose_name_plural = 'hr profile'

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    inlines = (HRProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(Department)
admin.site.register(Designation)

# Optionally, register HRProfile directly if you want it editable separately
# admin.site.register(HRProfile)