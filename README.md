# EDS Alarm Monitor

A web application that monitors EDS API for system alarms, providing comprehensive real-time notification and tracking capabilities.

## Features

- Real-time monitoring of EDS API for alarm events
- SMS notifications via Twilio for critical and high-priority alarms
- Web dashboard for alarm status and history
- Contact management for SMS recipients
- API credential configuration
- Automatic system alarm generation for API connection failures
- Alarm deduplication and filtering
- "Clear Alarms" functionality to reset and refresh alarm state

## Requirements

- Python 3.11+
- PostgreSQL database
- Twilio account for SMS notifications
- EDS API credentials

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   - `DATABASE_URL`: PostgreSQL connection string
   - `SESSION_SECRET`: Secret key for session management
   - Optional environment variables (normally stored in credentials database):
     - `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
     - `EDS_API_URL`, `EDS_API_USERNAME`, `EDS_API_PASSWORD`

## Running the Application

```bash
# Run the main application
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app
```

## Testing with Mock EDS API

For development and testing purposes, you can use the included mock EDS API server instead of connecting to a real EDS API. This allows comprehensive testing of all features without needing real EDS API credentials.

### Option 1: Using the dedicated test server script

```bash
# Start the mock EDS API server (in a separate terminal)
python run_test_server.py

# The mock server runs on port 3000 by default
# Configure the EDS Alarm Monitor to use the mock server:
# - API URL: http://localhost:3000 (on local machine)
#          or http://127.0.0.1:3000 (in Replit environment)
# - Username: test
# - Password: test
```

### Option 2: Running the mock server directly

```bash
# Start the mock EDS API server directly
python mock_eds_api.py
```

### Implementation Details

The mock server (`mock_eds_api.py`) is a Flask application that mimics the EDS API endpoints:
- `/api/v1/login`: Provides authentication with any username/password
- `/api/v1/logout`: Cleans up sessions
- `/api/v1/ping`: Confirms connection is active
- `/api/v1/events/read`: Generates random alarm events, including at least one high-priority alarm

The mock server generates new alarms with every request and maintains them in memory, ensuring your notification system can be fully tested before connecting to a production EDS API.

## Architecture

### Components

1. **Web Application** (`main.py`, `app.py`): Flask-based web interface and API
2. **API Connectors**:
   - `eds_api.py`: EDS API integration for retrieving alarms
   - `notification_service.py`: Twilio SMS integration
3. **Database Models** (`models.py`):
   - `ApiCredential`: Storage for API credentials
   - `ContactNumber`: SMS recipient details 
   - `AlarmEvent`: Alarm data and history
4. **Mock Server** (`mock_eds_api.py`): Mock EDS API for testing
5. **Scheduler**: Background task scheduler for periodic alarm checks

### Workflow

1. The system periodically checks for new alarms from the EDS API
2. New alarms are stored in the database
3. High-priority alarms trigger SMS notifications via Twilio
4. The web interface displays alarm status and history
5. Users can manage contacts and API credentials via the web interface
6. System alarms are generated for API connection failures
7. Alarms can be cleared and reset via the "Clear Alarms" button

## API Reference

### EDS API

The system integrates with the EDS API, which provides alarm events through the following endpoints:

- `/api/v1/login`: Authentication
- `/api/v1/logout`: Session termination
- `/api/v1/ping`: Connection verification
- `/api/v1/events/read`: Retrieve alarm events

### Internal API

The application provides internal API endpoints:

- `/api/alarms/recent`: Get recent alarms for AJAX refresh
- `/api/alarms/clear`: Clear all current alarms
- `/api/status`: Get current connection status