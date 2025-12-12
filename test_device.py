# {'user_id': '5', 'timestamp': '2025-12-08 19:09:56', 'status': 15}
# {'user_id': '21', 'timestamp': '2025-12-08 19:10:05', 'status': 1}
# {'user_id': '224', 'timestamp': '2025-12-08 19:10:13', 'status': 1}
# {'user_id': '293', 'timestamp': '2025-12-08 19:10:21', 'status': 1}
# {'user_id': '172', 'timestamp': '2025-12-08 19:15:57', 'status': 1}
# {'user_id': '207', 'timestamp': '2025-12-08 19:16:03', 'status': 1}
# {'user_id': '297', 'timestamp': '2025-12-08 19:16:06', 'status': 1}
# {'user_id': '131', 'timestamp': '2025-12-08 19:16:09', 'status': 1}
# {'user_id': '118', 'timestamp': '2025-12-08 19:16:13', 'status': 1}
# {'user_id': '244', 'timestamp': '2025-12-08 19:16:15', 'status': 1}
# {'user_id': '295', 'timestamp': '2025-12-08 19:16:40', 'status': 1}
# {'user_id': '263', 'timestamp': '2025-12-08 19:17:22', 'status': 15}
# {'user_id': '155', 'timestamp': '2025-12-08 19:17:28', 'status': 1}
# {'user_id': '134', 'timestamp': '2025-12-08 19:23:05', 'status': 1}
# {'user_id': '41', 'timestamp': '2025-12-08 19:27:43', 'status': 1}
# {'user_id': '304', 'timestamp': '2025-12-08 19:29:51', 'status': 1}
# {'user_id': '304', 'timestamp': '2025-12-08 19:29:56', 'status': 15}
# {'user_id': '304', 'timestamp': '2025-12-08 19:29:58', 'status': 15}
# {'user_id': '292', 'timestamp': '2025-12-08 19:30:12', 'status': 1}
# {'user_id': '89', 'timestamp': '2025-12-08 19:30:35', 'status': 1}
# {'user_id': '189', 'timestamp': '2025-12-08 19:38:25', 'status': 1}
# {'user_id': '151', 'timestamp': '2025-12-08 19:38:36', 'status': 1}
# {'user_id': '237', 'timestamp': '2025-12-08 19:48:24', 'status': 1}
# {'user_id': '69', 'timestamp': '2025-12-08 20:01:37', 'status': 1}
# {'user_id': '289', 'timestamp': '2025-12-08 20:01:46', 'status': 1}
# {'user_id': '289', 'timestamp': '2025-12-08 20:01:58', 'status': 15}
# {'user_id': '287', 'timestamp': '2025-12-08 20:02:07', 'status': 15}
# {'user_id': '287', 'timestamp': '2025-12-08 20:02:09', 'status': 15}
# {'user_id': '46', 'timestamp': '2025-12-08 20:14:03', 'status': 1}
# {'user_id': '260', 'timestamp': '2025-12-08 20:15:37', 'status': 1}
# {'user_id': '44', 'timestamp': '2025-12-08 20:15:45', 'status': 15}
# {'user_id': '44', 'timestamp': '2025-12-08 20:15:47', 'status': 15}
# {'user_id': '45', 'timestamp': '2025-12-08 20:20:22', 'status': 1}
# {'user_id': '202', 'timestamp': '2025-12-08 20:44:43', 'status': 15}
# {'user_id': '202', 'timestamp': '2025-12-08 20:44:45', 'status': 15}
# {'user_id': '286', 'timestamp': '2025-12-08 20:46:02', 'status': 15}
# {'user_id': '121', 'timestamp': '2025-12-08 20:46:09', 'status': 1}
# {'user_id': '198', 'timestamp': '2025-12-08 20:46:36', 'status': 1}
# {'user_id': '258', 'timestamp': '2025-12-08 20:46:41', 'status': 1}
# {'user_id': '72', 'timestamp': '2025-12-08 20:46:46', 'status': 1}
# {'user_id': '259', 'timestamp': '2025-12-08 20:46:52', 'status': 1}
# {'user_id': '114', 'timestamp': '2025-12-08 20:46:57', 'status': 1}
# {'user_id': '99', 'timestamp': '2025-12-08 20:47:11', 'status': 1}
# {'user_id': '111', 'timestamp': '2025-12-08 20:47:25', 'status': 1}
# {'user_id': '10', 'timestamp': '2025-12-08 20:47:36', 'status': 15}
# {'user_id': '62', 'timestamp': '2025-12-08 21:37:43', 'status': 15}
# {'user_id': '298', 'timestamp': '2025-12-08 21:38:02', 'status': 1}

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
