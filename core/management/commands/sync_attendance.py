from django.core.management.base import BaseCommand
from core.models import Employee, Attendance, AttendanceDevice
from zk import ZK
from datetime import datetime, timedelta, date, time
from django.utils import timezone
import pytz

class Command(BaseCommand):
    help = 'Syncs attendance data from ZK devices for a specific date (default: yesterday)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to sync in YYYY-MM-DD format. Defaults to yesterday.',
        )
        parser.add_argument(
            '--device',
            type=int,
            help='ID of a specific device to sync.',
        )

    def handle(self, *args, **options):
        # Determine date to sync
        target_date_str = options['date']
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid date format. Use YYYY-MM-DD.'))
                return
        else:
            # Default to yesterday
            target_date = datetime.now().date() - timedelta(days=1)
        
        self.stdout.write(f"Syncing attendance for: {target_date}")

        # Get devices
        device_id = options['device']
        if device_id:
            devices = AttendanceDevice.objects.filter(id=device_id, is_active=True)
        else:
            devices = AttendanceDevice.objects.filter(is_active=True)

        if not devices.exists():
            self.stdout.write(self.style.WARNING("No active devices found."))
            return

        for device in devices:
            self.sync_device(device, target_date)

    def sync_device(self, device, target_date):
        self.stdout.write(f"Connecting to {device.name} ({device.ip_address})...")
        conn = None
        zk = ZK(device.ip_address, port=device.port, timeout=10)
        
        try:
            conn = zk.connect()
            self.stdout.write(self.style.SUCCESS(f"Connected to {device.name}"))
            
            # Update last activity
            device.last_activity = timezone.now()
            device.save()

            # optimized: Get all logs (ZK library might not support filtering by date on fetch, so we fetch all and filter in python)
            # Note: In production with millions of logs, this might need optimization or clearing device logs
            logs = conn.get_attendance()
            
            # Group punches by user
            user_punches = {}

            for log in logs:
                # log.timestamp is a datetime object
                log_date = log.timestamp.date()
                
                if log_date == target_date:
                    user_id = str(log.user_id) # Ensure string for consistent mapping
                    if user_id not in user_punches:
                        user_punches[user_id] = []
                    user_punches[user_id].append(log.timestamp.time())

            self.process_punches(user_punches, target_date)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error syncing {device.name}: {e}"))
        finally:
            if conn:
                try:
                    conn.disconnect()
                except:
                    pass

    def process_punches(self, user_punches, target_date):
        count = 0
        for user_id, times in user_punches.items():
            try:
                # Find Employee by employee_code
                # Assumes ZK user_id matches Employee.employee_code
                employee = Employee.objects.get(employee_code=user_id)
                
                if not times:
                    continue

                # Sort times to find first and last punch
                times.sort()
                check_in = times[0]
                check_out = times[-1] if len(times) > 1 else None

                # Create or Update Attendance Record based on strict uniqueness
                # We use update_or_create to handle re-runs safely
                obj, created = Attendance.objects.update_or_create(
                    employee=employee,
                    date=target_date,
                    defaults={
                        'check_in_time': check_in,
                        'check_out_time': check_out,
                        'notes': 'Synced via Automation'
                    }
                )
                
                action = "Created" if created else "Updated"
                # self.stdout.write(f"  - {employee.full_name}: {action} (In: {check_in}, Out: {check_out})")
                count += 1

            except Employee.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  - Skipped User ID {user_id}: Employee not found in DB"))
                continue
        
        self.stdout.write(self.style.SUCCESS(f"Processed {count} records for {target_date}"))
