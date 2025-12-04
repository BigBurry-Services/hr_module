@echo off
setlocal enabledelayedexpansion

:: Log start time
echo ==== Django Task Started at %date% %time% ==== >> C:\HrModule\django_log.txt

:: Activate virtual environment
call "E:\hrmodule\hr_module\env\Scripts\activate.bat" >> C:\HrModule\django_log.txt 2>&1

:: Go to the Django project directory
cd /d "E:\hrmodule\hr_module\hr_module" >> C:\HrModule\django_log.txt 2>&1

:: Run server (or your command)
python manage.py runserver 0.0.0.0:80 >> C:\HrModule\django_log.txt 2>&1

:: Log end time
echo ==== Django Task Ended at %date% %time% ==== >> C:\HrModule\django_log.txt

exit
