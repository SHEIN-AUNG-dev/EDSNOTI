import logging
from dotenv import load_dotenv
from app import app
from models import db, ApiCredential, ContactNumber, AlarmEvent
import eds_api
import notification_service
from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_apscheduler import APScheduler
import datetime
import json

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

def get_credentials(api_type):
    """Retrieve API credentials from the database."""
    return ApiCredential.query.filter_by(api_type=api_type).first()

def get_active_contacts():
    """Retrieve active contact numbers for notifications."""
    return ContactNumber.query.filter_by(active=True).all()


def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.isoformat()
    raise TypeError("Object of type '%s' is not JSON serializable" % type(o).__name__)


def create_system_alarm(alarm_id, description, severity="HIGH"):
    """Create a system alarm event."""
    system_alarm = AlarmEvent(
        alarm_id=alarm_id,
        description=description,
        source="Alarm Monitor System",
        event_time=datetime.datetime.now(),
        severity=severity,
        status="ACTIVE",
        raw_data=json.dumps({"message": description, "type": "system"}, default=datetime_converter)
    )
    db.session.add(system_alarm)
    db.session.commit()
    return system_alarm

def send_sms_notifications(contacts, message, twilio_creds):
    """Send SMS notifications to contacts."""
    for contact in contacts:
        try:
            notification_service.send_sms(
                twilio_creds.username,  # Account SID
                twilio_creds.api_key,   # Auth Token
                twilio_creds.api_secret,  # Twilio Phone Number
                contact.phone_number,
                message
            )
            logger.info(f"Notification sent to {contact.phone_number}")
        except Exception as e:
            logger.error(f"Failed to send SMS to {contact.phone_number}: {str(e)}")

def check_alarms():
    """Check for new alarms from EDS API and send notifications."""
    try:
        eds_creds = get_credentials('eds')
        if not eds_creds:
            logger.warning("No EDS API credentials found")
            return

        twilio_creds = get_credentials('twilio')
        if not twilio_creds:
            logger.warning("No Twilio API credentials found")
            return

        contacts = get_active_contacts()
        if not contacts:
            logger.warning("No active contact numbers found for notifications")
            return

        last_timestamp_key = "last_check_timestamp"
        last_timestamp = app.config.pop(last_timestamp_key, None)
        if last_timestamp:
            logger.info(f"Using reset timestamp for alarm check: {last_timestamp}")
        else:
            latest_alarm = AlarmEvent.query.order_by(AlarmEvent.event_time.desc()).first()
            last_timestamp = latest_alarm.event_time if latest_alarm else None

        connection_successful = eds_api.check_connection(eds_creds.api_url, eds_creds.username, eds_creds.api_key)

        if connection_successful:
            system_alarms = AlarmEvent.query.filter(
                AlarmEvent.alarm_id == "SYSTEM-EDS-OFFLINE",
                AlarmEvent.status == "ACTIVE"
            ).all()
            if system_alarms:
                logger.info("Connection to EDS restored, clearing offline system alarms")
                for alarm in system_alarms:
                    alarm.status = "CLEARED"
                db.session.commit()
        else:
            logger.error("EDS API connection failed")
            system_alarm = create_system_alarm("SYSTEM-EDS-OFFLINE", "EDS API Connection Failed")
            recent_system_alarm = AlarmEvent.query.filter(
                AlarmEvent.alarm_id == "SYSTEM-EDS-OFFLINE",
                AlarmEvent.status == "ACTIVE",
                AlarmEvent.event_time >= datetime.datetime.now() - datetime.timedelta(hours=1)
            ).first()
            if not recent_system_alarm or recent_system_alarm.id == system_alarm.id:
                send_sms_notifications(contacts, "ALARM: EDS API is offline - Monitoring System - HIGH", twilio_creds)
            return

        new_alarms = eds_api.get_alarm_events(
            eds_creds.api_url,
            eds_creds.username,
            eds_creds.api_key,
            last_timestamp
        )

        if not new_alarms:
            logger.info("No new alarms found")
            return

        logger.info(f"Found {len(new_alarms)} new alarms")

        for alarm in new_alarms:
            new_alarm = AlarmEvent(
                alarm_id=alarm['id'],
                description=alarm['description'],
                source=alarm['source'],
                event_time=alarm['timestamp'],
                severity=alarm['severity'],
                status=alarm['status'],
                raw_data=json.dumps(alarm, default=datetime_converter)
            )
            db.session.add(new_alarm)

            if alarm['severity'] in ['HIGH', 'CRITICAL']:
                message = f"ALARM: {alarm['description']} - {alarm['source']} - {alarm['severity']}"
                send_sms_notifications(contacts, message, twilio_creds)

        db.session.commit()

    except Exception as e:
        logger.error(f"Error in check_alarms job: {str(e)}")
        system_alarm = create_system_alarm("SYSTEM-EDS-ERROR", f"EDS API Error: {str(e)[:100]}")
        recent_system_alarm = AlarmEvent.query.filter(
            AlarmEvent.alarm_id == "SYSTEM-EDS-ERROR",
            AlarmEvent.status == "ACTIVE",
            AlarmEvent.event_time >= datetime.datetime.now() - datetime.timedelta(hours=1)
        ).first()
        if not recent_system_alarm or recent_system_alarm.id == system_alarm.id:
            send_sms_notifications(contacts, f"ALARM: EDS API Error - {str(e)[:50]}... - HIGH", twilio_creds)

@scheduler.task('interval', id='check_alarms_job', seconds=60, misfire_grace_time=900)
def scheduled_alarm_check():
    """Scheduled task to check for alarms every minute."""
    with app.app_context():
        check_alarms()

@app.route('/')
def index():
    """Dashboard home page."""
    eds_status = "Unknown"
    eds_creds = get_credentials('eds')
    if eds_creds:
        try:
            if eds_api.check_connection(eds_creds.api_url, eds_creds.username, eds_creds.api_key):
                eds_status = "Connected"
            else:
                eds_status = "Failed"
        except Exception:
            eds_status = "Error"

    twilio_status = "Unknown"
    twilio_creds = get_credentials('twilio')
    if twilio_creds:
        try:
            if notification_service.check_connection(twilio_creds.username, twilio_creds.api_key):
                twilio_status = "Connected"
            else:
                twilio_status = "Failed"
        except Exception:
            twilio_status = "Error"

    latest_system_alarms_subquery = db.session.query(
        AlarmEvent.alarm_id,
        db.func.max(AlarmEvent.event_time).label('max_time')
    ).filter(
        AlarmEvent.alarm_id.like('SYSTEM-%'),
        AlarmEvent.status == 'ACTIVE'
    ).group_by(
        AlarmEvent.alarm_id
    ).subquery()

    recent_alarms_query = AlarmEvent.query.outerjoin(
        latest_system_alarms_subquery,
        db.and_(
            AlarmEvent.alarm_id == latest_system_alarms_subquery.c.alarm_id,
            AlarmEvent.event_time == latest_system_alarms_subquery.c.max_time
        )
    ).filter(
        AlarmEvent.status == 'ACTIVE',
        db.or_(
            ~AlarmEvent.alarm_id.like('SYSTEM-%'),
            db.and_(
                AlarmEvent.alarm_id == latest_system_alarms_subquery.c.alarm_id,
                AlarmEvent.event_time == latest_system_alarms_subquery.c.max_time
            )
        )
    )

    recent_alarms = recent_alarms_query.order_by(AlarmEvent.event_time.desc()).limit(5).all()

    return render_template('index.html', 
        eds_status=eds_status, 
        twilio_status=twilio_status, 
        recent_alarms=recent_alarms,
        now=datetime.datetime.now()
    )

@app.route('/alarms')
def alarms():
    """View all alarms."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    status_filter = request.args.get('status', 'ACTIVE')

    latest_system_alarms_subquery = db.session.query(
        AlarmEvent.alarm_id,
        db.func.max(AlarmEvent.event_time).label('max_time')
    ).filter(
        AlarmEvent.alarm_id.like('SYSTEM-%')
    ).group_by(
        AlarmEvent.alarm_id
    ).subquery()

    query = AlarmEvent.query.outerjoin(
        latest_system_alarms_subquery,
        db.and_(
            AlarmEvent.alarm_id == latest_system_alarms_subquery.c.alarm_id,
            AlarmEvent.event_time == latest_system_alarms_subquery.c.max_time
        )
    )

    if status_filter != 'ALL':
        query = query.filter(AlarmEvent.status == status_filter)

    query = query.filter(
        db.or_(
            ~AlarmEvent.alarm_id.like('SYSTEM-%'),
            db.and_(
                AlarmEvent.alarm_id == latest_system_alarms_subquery.c.alarm_id,
                AlarmEvent.event_time == latest_system_alarms_subquery.c.max_time
            )
        )
    )

    alarms = query.order_by(AlarmEvent.event_time.desc()).paginate(page=page, per_page=per_page)

    status_options = ['ACTIVE', 'CLEARED', 'ACKNOWLEDGED', 'ALL']

    return render_template('alarms.html', 
                          alarms=alarms, 
                          status_filter=status_filter,
                          status_options=status_options,
                          now=datetime.datetime.now())

@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    """Manage contact numbers."""
    if request.method == 'POST':
        if 'add_contact' in request.form:
            name = request.form.get('name')
            phone_number = request.form.get('phone_number')

            if not name or not phone_number:
                flash('Name and phone number are required', 'danger')
            else:
                contact = ContactNumber(name=name, phone_number=phone_number, active=True)
                db.session.add(contact)
                db.session.commit()
                flash('Contact added successfully', 'success')

        elif 'delete_contact' in request.form:
            contact_id = request.form.get('contact_id')
            contact = ContactNumber.query.get(contact_id)
            if contact:
                db.session.delete(contact)
                db.session.commit()
                flash('Contact deleted successfully', 'success')

        elif 'toggle_contact' in request.form:
            contact_id = request.form.get('contact_id')
            contact = ContactNumber.query.get(contact_id)
            if contact:
                contact.active = not contact.active
                db.session.commit()
                status = "activated" if contact.active else "deactivated"
                flash(f'Contact {status} successfully', 'success')

        return redirect(url_for('contacts'))

    contacts = ContactNumber.query.all()
    return render_template('contacts.html', contacts=contacts, now=datetime.datetime.now())

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    """Manage API credentials."""
    if request.method == 'POST':
        api_type = request.form.get('api_type')
        api_url = request.form.get('api_url', '')
        username = request.form.get('username', '')
        api_key = request.form.get('api_key', '')
        api_secret = request.form.get('api_secret', '')

        if not api_type or not username or not api_key:
            flash('API type, username, and API key/password are required', 'danger')
        else:
            credential = get_credentials(api_type)

            if credential:
                credential.api_url = api_url
                credential.username = username
                credential.api_key = api_key
                credential.api_secret = api_secret
            else:
                credential = ApiCredential(
                    api_type=api_type,
                    api_url=api_url,
                    username=username,
                    api_key=api_key,
                    api_secret=api_secret
                )
                db.session.add(credential)

            db.session.commit()
            flash(f'{api_type.upper()} API credentials updated successfully', 'success')

        return redirect(url_for('settings'))

    eds_creds = get_credentials('eds')
    twilio_creds = get_credentials('twilio')

    return render_template('settings.html', eds_creds=eds_creds, twilio_creds=twilio_creds, now=datetime.datetime.now())

@app.route('/api/alarms/recent')
def api_recent_alarms():
    """API endpoint to get recent alarms for Ajax refresh."""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.datetime.now() - datetime.timedelta(hours=hours)

        latest_system_alarms_subquery = db.session.query(
            AlarmEvent.alarm_id,
            db.func.max(AlarmEvent.event_time).label('max_time')
        ).filter(
            AlarmEvent.alarm_id.like('SYSTEM-%'),
            AlarmEvent.event_time >= since
        ).group_by(
            AlarmEvent.alarm_id
        ).subquery()

        alarms = AlarmEvent.query.outerjoin(
            latest_system_alarms_subquery,
            db.and_(
                AlarmEvent.alarm_id == latest_system_alarms_subquery.c.alarm_id,
                AlarmEvent.event_time == latest_system_alarms_subquery.c.max_time
            )
        ).filter(
            db.and_(
                AlarmEvent.event_time >= since,
                db.or_(
                    ~AlarmEvent.alarm_id.like('SYSTEM-%'),
                    db.and_(
                        AlarmEvent.alarm_id == latest_system_alarms_subquery.c.alarm_id,
                        AlarmEvent.event_time == latest_system_alarms_subquery.c.max_time
                    )
                )
            )
        ).order_by(AlarmEvent.event_time.desc()).all()

        result = []
        for alarm in alarms:
            result.append({
                'id': alarm.id,
                'alarm_id': alarm.alarm_id,
                'description': alarm.description,
                'source': alarm.source,
                'event_time': alarm.event_time.isoformat(),
                'severity': alarm.severity,
                'status': alarm.status
            })

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting recent alarms: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint to get the current connection status."""
    try:
        result = {
            'eds': 'Unknown',
            'twilio': 'Unknown'
        }

        eds_creds = get_credentials('eds')
        if eds_creds:
            try:
                if eds_api.check_connection(eds_creds.api_url, eds_creds.username, eds_creds.api_key):
                    result['eds'] = 'Connected'
                else:
                    result['eds'] = 'Failed'
            except Exception:
                result['eds'] = 'Error'

        twilio_creds = get_credentials('twilio')
        if twilio_creds:
            try:
                if notification_service.check_connection(twilio_creds.username, twilio_creds.api_key):
                    result['twilio'] = 'Connected'
                else:
                    result['twilio'] = 'Failed'
            except Exception:
                result['twilio'] = 'Error'

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting API status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/alarms/clear', methods=['POST'])
def clear_alarms():
    """API endpoint to clear all current alarms."""
    try:
        AlarmEvent.query.update({AlarmEvent.status: 'CLEARED'})
        db.session.commit()

        system_alarms = AlarmEvent.query.filter(AlarmEvent.alarm_id.like('SYSTEM-%')).all()
        for alarm in system_alarms:
            db.session.delete(alarm)
        db.session.commit()

        last_timestamp_key = "last_check_timestamp"
        app.config[last_timestamp_key] = datetime.datetime.now() - datetime.timedelta(hours=24)
        logger.info(f"Alarm timestamp reset to: {app.config[last_timestamp_key]}")

        db.session.commit()
        logger.info("All alarms have been cleared, timestamp reset to check all alarms")

        logger.info("Running immediate alarm check after clear...")
        with app.app_context():
            check_alarms()

        return jsonify({'success': True, 'message': 'All alarms cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing alarms: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
