"""
Mock EDS API for testing the alarm monitor system
This is a simple Flask app that mimics the EDS API endpoints
"""
import os
import random
import time
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for sessions and alarms
sessions = {}
alarms = []

# Generate some sample alarms
alarm_sources = ["Server Room", "Network Switch", "Database", "Application Server", "Power Supply"]
alarm_descriptions = [
    "Temperature threshold exceeded",
    "Network connectivity lost",
    "Database performance degraded",
    "CPU utilization high",
    "Disk space critical",
    "Memory usage above threshold",
    "Power supply failure",
    "Backup process failed",
    "Security alert detected",
    "Service unavailable"
]
alarm_priorities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
alarm_statuses = ["ACTIVE", "CLEARED", "ACKNOWLEDGED"]

# Generate some initial alarms
for i in range(20):
    # Create some alarms in the past week
    timestamp = datetime.now() - timedelta(days=random.randint(0, 7), 
                                         hours=random.randint(0, 23), 
                                         minutes=random.randint(0, 59))
    
    alarm = {
        "id": f"ALARM-{i+1000}",
        "source": random.choice(alarm_sources),
        "description": random.choice(alarm_descriptions),
        "timestamp": int(timestamp.timestamp()),
        "priority": random.choice(alarm_priorities),
        "status": random.choice(alarm_statuses),
        "metadata": {
            "location": "Building A",
            "system": "Production",
            "type": "Environmental" if "Temperature" in alarm_descriptions else "System"
        }
    }
    
    alarms.append(alarm)

# Sort alarms by timestamp (newest first)
alarms.sort(key=lambda x: x["timestamp"], reverse=True)

@app.route('/api/v1/login', methods=['POST'])
def login():
    """Mock login endpoint"""
    data = request.json
    
    # Check credentials (accept any for testing)
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 401
    
    # Generate a session ID
    session_id = f"sess_{int(time.time())}_{random.randint(1000, 9999)}"
    sessions[session_id] = {
        "username": username,
        "created": datetime.now(),
        "expires": datetime.now() + timedelta(hours=1)
    }
    
    return jsonify({
        "sessionId": session_id,
        "user": username,
        "expires": int((datetime.now() + timedelta(hours=1)).timestamp())
    })

@app.route('/api/v1/logout', methods=['POST'])
def logout():
    """Mock logout endpoint"""
    # Get session from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Invalid authorization"}), 401
    
    session_id = auth_header.split(' ')[1]
    
    # Remove session
    if session_id in sessions:
        del sessions[session_id]
    
    return jsonify({"status": "success"})

@app.route('/api/v1/ping', methods=['GET'])
def ping():
    """Mock ping endpoint to verify session"""
    # Get session from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Invalid authorization"}), 401
    
    session_id = auth_header.split(' ')[1]
    
    # Verify session exists
    if session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 401
    
    return jsonify({"status": "ok"})

@app.route('/api/v1/events/read', methods=['POST'])
def events_read():
    """Mock events endpoint to retrieve alarm events"""
    # Get session from Authorization header
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"error": "Invalid authorization"}), 401
    
    session_id = auth_header.split(' ')[1]
    
    # Verify session exists
    if session_id not in sessions:
        return jsonify({"error": "Invalid session"}), 401
    
    # Get filters from request
    data = request.json
    filters = data.get('filters', [])
    
    # Apply timestamp filter if provided
    filtered_alarms = alarms
    for filter_item in filters:
        if 'ts' in filter_item and 'from' in filter_item['ts']:
            from_ts = filter_item['ts']['from']
            filtered_alarms = [a for a in filtered_alarms if a['timestamp'] >= from_ts]
    
    # Always create a new alarm with current timestamp
    # And ensure it's HIGH priority to trigger notifications
    new_alarm = {
        "id": f"ALARM-{int(time.time())}-{random.randint(1000, 9999)}",
        "source": random.choice(alarm_sources),
        "description": random.choice(alarm_descriptions),
        "timestamp": int(datetime.now().timestamp()),
        "priority": "HIGH",  # Force HIGH priority to trigger notification
        "status": "ACTIVE",  # New alarms are always active
        "metadata": {
            "location": "Building A",
            "system": "Production",
            "type": "Environmental" if "Temperature" in alarm_descriptions else "System"
        }
    }
    
    # Add to global alarms list
    alarms.insert(0, new_alarm)
    
    # If it's after the filter timestamp, add to results
    if not filters or not any('ts' in f for f in filters) or new_alarm['timestamp'] >= filters[0]['ts']['from']:
        filtered_alarms.insert(0, new_alarm)
    
    return jsonify({
        "events": filtered_alarms,
        "total": len(filtered_alarms)
    })

if __name__ == '__main__':
    port = int(os.environ.get('MOCK_EDS_PORT', 3000))
    
    print(f"""
==================================================
MOCK EDS API SERVER RUNNING ON PORT {port}
==================================================

To use this mock API server with the EDS Alarm Monitor:

1. Set these API credentials in the monitor settings:
   - API URL: http://localhost:{port}  (on local machine)
            or http://127.0.0.1:{port} (in Replit environment)
   - Username: test
   - Password: test
   
2. The mock server will generate random alarms
   and ensure at least one HIGH priority alarm
   to test notifications
   
3. Press Ctrl+C to stop the server

==================================================
""")
    
    app.run(host='0.0.0.0', port=port, debug=True)