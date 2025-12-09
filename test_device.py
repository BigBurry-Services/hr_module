from zk import ZK
from datetime import datetime, timedelta

device_ip = "192.168.1.210"

zk = ZK(device_ip, port=4370, timeout=10, password=0)

try:
    conn = zk.connect()
    print("Connected!")

    # Get all logs
    print('getting logs from system')
    logs = conn.get_attendance()

    # Calculate yesterday's date (00:00 to 23:59)
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    print(f"\nAttendance for: {yesterday}\n")

    for log in logs:
        log_date = log.timestamp.date()

        if log_date == yesterday:
            print({
                "user_id": log.user_id,
                "timestamp": log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "status": log.status,
                # "punch": log.punch
            })

    conn.disconnect()

except Exception as e:
    print("Error:", e)
