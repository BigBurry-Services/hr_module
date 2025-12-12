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
        
        from core.utils import DeviceSyncService
        service = DeviceSyncService()
        results = service.sync_devices(target_date=target_date, device_id=device_id)

        for error in results['errors']:
            self.stdout.write(self.style.ERROR(error))
        
        if results['devices_connected'] == 0 and not results['errors']:
             self.stdout.write(self.style.WARNING("No active devices found."))

        self.stdout.write(self.style.SUCCESS(f"Processed {results['processed_count']} records for {target_date}"))
