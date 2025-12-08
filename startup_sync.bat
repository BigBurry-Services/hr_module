@echo off
cd /d "e:\BIGBURRY\SERVICES\Ashiq hr module\hr_module"
call env\Scripts\activate.bat
echo Starting Attendance Sync...
python manage.py sync_attendance --date %DATE%
echo Sync Completed.
pause
