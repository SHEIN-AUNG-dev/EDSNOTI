
from app import app, db
from models import AlarmEvent

def clear_alarm_events():
    with app.app_context():
        try:
            # Delete all alarm events
            AlarmEvent.query.delete()
            db.session.commit()
            print("Successfully cleared all alarm events from database")
        except Exception as e:
            print(f"Error clearing alarm events: {e}")
            db.session.rollback()

if __name__ == "__main__":
    clear_alarm_events()
