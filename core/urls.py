from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('employee-dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('login/', views.login_view, name='login'),
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # HR Management (Admin Only)
    path('site-admin/hr/manage/', views.manage_hrs, name='manage_hrs'),
    path('site-admin/hr/add/', views.manage_hr_add, name='manage_hr_add'),
    path('site-admin/hr/<int:pk>/edit/', views.manage_hr_edit, name='manage_hr_edit'),
    path('site-admin/hr/<int:pk>/delete/', views.manage_hr_delete, name='manage_hr_delete'),
    path('site-admin/hr/<int:pk>/toggle-status/', views.toggle_user_status, name='toggle_user_status'),

    # Department and Designation Management URLs
    path('departments/', views.department_list, name='department_list'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    path('designations/', views.designation_list, name='designation_list'),
    path('designations/<int:pk>/edit/', views.designation_edit, name='designation_edit'),
    path('designations/<int:pk>/delete/', views.designation_delete, name='designation_delete'),

    # Allowance Management URLs
    path('allowances/', views.allowance_list, name='allowance_list'),
    path('allowances/<int:pk>/edit/', views.allowance_edit, name='allowance_edit'),
    path('allowances/<int:pk>/delete/', views.allowance_delete, name='allowance_delete'),

    # Employee Management URLs
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_add, name='employee_add'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_edit, name='employee_edit'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),

    # Attendance Management URLs
    path('attendance/mark/', views.attendance_mark, name='attendance_mark'),
    path('attendance/update-single/<int:employee_id>/', views.update_single_attendance, name='update_single_attendance'),
    path('attendance/mark_leave/<int:employee_id>/', views.mark_single_leave, name='mark_single_leave'),
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    
    # Device Management URLs (Replaces old sync)
    path('devices/', views.device_list, name='device_list'),
    path('devices/<int:pk>/edit/', views.device_edit, name='device_edit'),
    path('devices/<int:pk>/delete/', views.device_delete, name='device_delete'),
    path('devices/<int:pk>/test/', views.device_test_connection, name='device_test_connection'),
    path('attendance/sync/', views.attendance_sync, name='attendance_sync'), # Redirects to device_list
    path('attendance/sync-devices/', views.sync_attendance_view, name='sync_attendance_from_devices'),

    # Export URLs
    path('employees/export/', views.export_employees_csv, name='export_employees_csv'),
    path('employees/<int:pk>/export/', views.export_single_employee_csv, name='export_single_employee_csv'),
    path('attendance/export/', views.export_attendance_csv, name='export_attendance_csv'),
    path('attendance/monthly-export/', views.export_monthly_attendance_csv, name='export_monthly_attendance_csv'),

    # Summary URL
    path('summary/', views.summary, name='summary'),
    path('attendance/toggle-lock/', views.toggle_attendance_lock, name='toggle_attendance_lock'),
    
    # Leaves & Reports
    path('leaves/calendar/', views.leave_calendar, name='leave_calendar'),
    path('attendance/toggle-no-break/<int:pk>/', views.toggle_no_break, name='toggle_no_break'),
    path('leaves/toggle-holiday/', views.toggle_holiday, name='toggle_holiday'),
    path('leaves/list/', views.leave_list, name='leave_list'),
    path('leaves/type/<int:pk>/edit/', views.leave_type_edit, name='leave_type_edit'),
    path('leaves/type/<int:pk>/delete/', views.leave_type_delete, name='leave_type_delete'),
    path('leaves/export/', views.export_leaves_csv, name='export_leaves_csv'),
    path('salary/advance/', views.salary_advance_list, name='salary_advance_list'),
    path('salary/advance/export/', views.export_salary_advances_csv, name='export_salary_advances_csv'),
    path('salary/monthly-report/', views.monthly_salary_report, name='monthly_salary_report'),
    path('salary/monthly-report/export/', views.export_monthly_salary_report, name='export_monthly_salary_report'),
    path('salary/toggle-status/', views.toggle_salary_status, name='toggle_salary_status'),
    path('salary/update-manual-adjustment/', views.update_manual_adjustment, name='update_manual_adjustment'),
]

