import logging
from datetime import datetime, timedelta, time
from django.utils import timezone
from zk import ZK
from .models import Employee, Attendance, AttendanceDevice

logger = logging.getLogger(__name__)

class DeviceSyncService:
    def sync_devices(self, target_date=None, device_id=None):
        """
        Syncs attendance from devices for a specific date.
        If no date is provided, defaults to yesterday.
        """
        if not target_date:
            target_date = datetime.now().date() - timedelta(days=1)
            
        results = {
            'processed_count': 0,
            'errors': [],
            'devices_connected': 0
        }

        devices = AttendanceDevice.objects.filter(is_active=True)
        if device_id:
            devices = devices.filter(id=device_id)

        if not devices.exists():
            results['errors'].append("No active devices found.")
            return results

        user_punches = {} # {user_id: [{'time': time, 'status': status}]}

        for device in devices:
            try:
                # print(f"Connecting to {device.name} ({device.ip_address})...")
                zk = ZK(device.ip_address, port=device.port, timeout=10)
                conn = zk.connect()
                # print(f"Connected to {device.name}")
                
                device.last_activity = timezone.now()
                device.save()
                results['devices_connected'] += 1

                logs = conn.get_attendance()
                
                for log in logs:
                    # log.timestamp is a datetime object
                    if log.timestamp.date() == target_date:
                        user_id = str(log.user_id)
                        if user_id not in user_punches:
                            user_punches[user_id] = []
                        
                        user_punches[user_id].append({
                            'time': log.timestamp.time(),
                            'status': log.status
                        })
                
                conn.disconnect()
            except Exception as e:
                error_msg = f"Error syncing {device.name}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        # Process accumulated punches
        count = self.process_punches(user_punches, target_date)
        results['processed_count'] = count
        
        return results

    def process_punches(self, user_punches, target_date):
        count = 0
        for user_id, punches in user_punches.items():
            try:
                # Find Employee by employee_code
                try:
                    employee = Employee.objects.get(employee_code=user_id)
                except Employee.DoesNotExist:
                    # Try removing leading zeros if simple match fails
                    if user_id.startswith('0'):
                         try:
                            employee = Employee.objects.get(employee_code=int(user_id))
                         except (Employee.DoesNotExist, ValueError):
                            continue
                    else:
                        continue

                if not punches:
                    continue

                # Sort punches by time
                punches.sort(key=lambda x: x['time'])
                
                check_in = None
                check_out = None
                
                # Logic: 
                # 1. Try to assume Status 1 is Check-In, Status 15 is Check-Out
                # 2. If timestamps are available but statuses are ambiguous, assume First is In, Last is Out
                
                # Filter for explicit status if multiple exist
                ins = [p['time'] for p in punches if p['status'] in [0, 1]] # assuming 0 might be default checkin too
                outs = [p['time'] for p in punches if p['status'] in [15, 2, 4, 5]] # 15 seems to be checkout from user data

                # Mixed Approach:
                # If we have explicit IN, use the first one. Else use the very first punch.
                if ins:
                    check_in = min(ins)
                else:
                    check_in = punches[0]['time'] # First punch of the day
                
                # If we have explicit OUT, use the last one.
                if outs:
                     check_out = max(outs)
                else:
                    # if we have multiple punches and no explicit out, assume last punch is out
                    if len(punches) > 1:
                        check_out = punches[-1]['time']

                # Create or Update Attendance
                obj, created = Attendance.objects.update_or_create(
                    employee=employee,
                    date=target_date,
                    defaults={
                        'check_in_time': check_in,
                        'check_out_time': check_out,
                        'notes': 'Synced via Device'
                    }
                )
                count += 1

            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}")
                continue
        
        return count
