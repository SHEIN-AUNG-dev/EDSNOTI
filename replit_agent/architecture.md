# Architecture Overview

## Overview

The EDS Alarm Monitor is a Flask-based web application designed to monitor alarms from an external data source (EDS) API and send SMS notifications via Twilio when critical alarms are detected. The application includes a dashboard for monitoring system status, viewing alarm history, managing contact information, and configuring API connections.

## System Architecture

The system follows a traditional web application architecture with:

1. **Backend**: Python Flask application handling business logic and data processing
2. **Frontend**: HTML templates with Bootstrap CSS for UI rendering
3. **Database**: SQL database (PostgreSQL) for data persistence
4. **External Services**: EDS API for alarm data and Twilio for SMS notifications
5. **Background Processing**: APScheduler for periodic alarm checking

```
+-------------+        +-----------------+        +----------------+
|             |        |                 |        |                |
| Web Browser |<------>| Flask App       |<------>| PostgreSQL DB  |
|             |        | (EDS Monitor)   |        |                |
+-------------+        +-----------------+        +----------------+
                              ^   ^
                              |   |
                              v   v
                     +--------+   +--------+
                     |                     |
                     v                     v
              +-------------+      +----------------+
              |             |      |                |
              | EDS API     |      | Twilio API     |
              | (Alarm Data)|      | (SMS Service)  |
              +-------------+      +----------------+
```

## Key Components

### Backend Components

1. **Flask Application (`main.py`, `app.py`):**
   - Main application entry point
   - Route definitions and request handling
   - Integration with external services

2. **Database Models (`models.py`):**
   - `ApiCredential`: Stores API credentials for EDS and Twilio
   - `ContactNumber`: Stores contact phone numbers for SMS notifications
   - `AlarmEvent`: Stores alarm events from the EDS API

3. **External API Integrations:**
   - `eds_api.py`: Handles communication with the EDS API for alarm data
   - `notification_service.py`: Manages Twilio SMS sending functionality

4. **Configuration (`config.py`):**
   - Environment-based configuration settings
   - API endpoints and credentials

5. **Background Processing:**
   - APScheduler for periodic alarm checks
   - Automatic notification dispatch for new alarms

### Frontend Components

1. **Templates:**
   - `base.html`: Base template with navigation and common layout
   - `index.html`: Dashboard showing system status
   - `alarms.html`: Alarm history display and filtering
   - `contacts.html`: Contact management for notifications
   - `settings.html`: System configuration for APIs

2. **Static Assets:**
   - `dashboard.js`: Client-side functionality for dashboard
   - `custom.css`: Custom styling for the application

## Data Flow

### Alarm Monitoring Flow

1. **Alarm Polling:**
   - Scheduler runs `check_alarms()` at configured intervals
   - Application retrieves EDS API credentials from database
   - Application authenticates with EDS API
   - Application requests new alarms since last check

2. **Alarm Processing:**
   - New alarms are stored in the database
   - Severity levels are evaluated (HIGH, MEDIUM, LOW)
   - Critical and high severity alarms trigger notifications

3. **Notification Flow:**
   - System retrieves active contacts from database
   - Twilio credentials are retrieved from database
   - SMS messages are constructed with alarm details
   - Notifications are sent through Twilio API
   - Delivery status is tracked and logged

### User Interface Flow

1. **Dashboard:**
   - Displays connection status for EDS and Twilio APIs
   - Shows alarm statistics and recent activity
   - Provides quick access to system functions

2. **Alarm Management:**
   - Lists historical alarms with filtering options
   - Allows viewing alarm details and metadata
   - Supports filtering by severity and status

3. **Contact Management:**
   - CRUD operations for notification recipients
   - Activation/deactivation of contacts
   - Contact listing and management

4. **Settings:**
   - API configuration for EDS and Twilio
   - Connection testing
   - System parameter configuration

## External Dependencies

### API Integrations

1. **EDS API:**
   - Used for retrieving alarm data
   - Requires authentication with username/password
   - Configured through the settings interface

2. **Twilio API:**
   - Used for sending SMS notifications
   - Requires account SID, auth token, and phone number
   - Configured through the settings interface

### Technology Stack

1. **Backend:**
   - Python 3.11+
   - Flask web framework
   - SQLAlchemy ORM
   - APScheduler for background tasks

2. **Frontend:**
   - HTML/CSS/JavaScript
   - Bootstrap CSS framework
   - Chart.js for data visualization
   - Font Awesome for icons

3. **Database:**
   - PostgreSQL (configured via environment variable)
   - SQLAlchemy for database operations

4. **External Libraries:**
   - `twilio`: Twilio API client for SMS
   - `requests`: HTTP client for API communication
   - `flask-apscheduler`: Flask integration for APScheduler
   - `psycopg2-binary`: PostgreSQL adapter for Python

## Deployment Strategy

The application is configured for deployment on Replit with the following characteristics:

1. **Deployment Target:**
   - Autoscaling deployment
   - Gunicorn WSGI server

2. **Environment Configuration:**
   - Environment variables for configuration
   - PostgreSQL database connection
   - Sensitive information management

3. **Runtime Environment:**
   - Python 3.11
   - OpenSSL and PostgreSQL packages
   - Dependency management via pyproject.toml

4. **Process Management:**
   - Gunicorn process binding to port 5000
   - Reuse port for hot reloading
   - Process monitoring and restart

5. **Workflow Configuration:**
   - Defined in .replit file
   - Automated startup process
   - Port exposure for web access

## Security Considerations

1. **Credential Management:**
   - API credentials stored in database
   - Environment variables for sensitive data
   - Secret key configuration for session management

2. **API Security:**
   - Connection pooling with ping checks
   - Timeouts for external API calls
   - Error handling for API failures

3. **Database Security:**
   - Connection pooling
   - Prepared statements via SQLAlchemy
   - Schema validation

## Future Expansion Considerations

1. **Scalability:**
   - The autoscaling deployment can handle increased load
   - Database connection pooling supports concurrent requests

2. **Additional Integrations:**
   - Structure allows for adding more notification channels
   - Model design supports additional API credential types

3. **Enhanced Monitoring:**
   - Architecture supports adding more detailed analytics
   - Historical data storage enables trend analysis