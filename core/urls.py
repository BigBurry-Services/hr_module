from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

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
    path('attendance/<int:pk>/edit/', views.attendance_edit, name='attendance_edit'),
    path('attendance/<int:pk>/delete/', views.attendance_delete, name='attendance_delete'),
    path('attendance/sync/', views.attendance_sync, name='attendance_sync'),

    # Summary URL
    path('summary/', views.summary, name='summary'),
]
