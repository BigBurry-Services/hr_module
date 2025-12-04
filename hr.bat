@echo off
setlocal enabledelayedexpansion

:: Log start time
echo ==== Django Task Started at %date% %time% ==== >> C:\test\django_log.txt

:: Activate virtual environment
call "E:\BIGBURRY\SERVICES\Ashiq hr module\hr_module\env\Scripts\activate.bat" >> C:\test\django_log.txt 2>&1

:: Go to the Django project directory
cd /d "E:\BIGBURRY\SERVICES\Ashiq hr module\hr_module" >> C:\test\django_log.txt 2>&1

:: Run server (or your command)
python manage.py runserver 0.0.0.0:8000 >> C:\test\django_log.txt 2>&1

:: Log end time
echo ==== Django Task Ended at %date% %time% ==== >> C:\test\django_log.txt

exit
