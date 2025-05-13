import logging
import requests
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Union

# Configure logging
logger = logging.getLogger(__name__)

class EDSApiError(Exception):
    """Exception raised for errors in the EDS API interactions."""
    pass

def login(base_url: str, username: str, password: str) -> str:
    """
    Authenticate with the EDS API and get a session token.
    
    Args:
        base_url: Base URL of the EDS API
        username: EDS API username
        password: EDS API password
        
    Returns:
        Session ID token
        
    Raises:
        EDSApiError: If authentication fails
    """
    try:
        # Make sure base_url is properly formatted
        if base_url and not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"
            
        url = f"{base_url}/api/v1/login"
        payload = {
            "username": username,
            "password": password,
            "type": "alarm-monitor"
        }
        
        response = requests.post(url, json=payload, timeout=2)
        
        if response.status_code != 200:
            logger.error(f"EDS API login failed: {response.status_code} -     {response.text}")
            raise EDSApiError(f"Login failed with status code {response.status_code}")
        
        data = response.json()
        session_id = data.get('sessionId')
        
        if not session_id:
            logger.error(f"EDS API login failed: No session ID returned - {response.text}")
            raise EDSApiError("Login failed: No session ID returned")
        
        return session_id
        
    except requests.RequestException as e:
        logger.error(f"EDS API request error during login: {str(e)}")
        raise EDSApiError(f"Request error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"EDS API JSON decode error during login: {str(e)}")
        raise EDSApiError(f"JSON decode error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during EDS API login: {str(e)}")
        raise EDSApiError(f"Unexpected error: {str(e)}")

def check_connection(base_url: str, username: str, password: str) -> bool:
    """
    Check if we can connect to the EDS API.
    
    Args:
        base_url: Base URL of the EDS API
        username: EDS API username
        password: EDS API password
        
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        # Try to authenticate
        session_id = login(base_url, username, password)
        
        # Ping to verify session
        url = f"{base_url}/api/v1/ping"
        headers = {
            "Authorization": f"Bearer {session_id}"
        }
        
        response = requests.get(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            # Logout to clean up
            logout(base_url, session_id)
            return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking EDS API connection: {str(e)}")
        return False

def logout(base_url: str, session_id: str) -> bool:
    """
    Log out from the EDS API.
    
    Args:
        base_url: Base URL of the EDS API
        session_id: Session ID from login
        
    Returns:
        True if logout was successful, False otherwise
    """
    try:
        url = f"{base_url}/api/v1/logout"
        headers = {
            "Authorization": f"Bearer {session_id}"
        }
        
        response = requests.post(url, headers=headers, timeout=2)
        
        if response.status_code == 200:
            return True
        
        logger.warning(f"EDS API logout failed: {response.status_code} - {response.text}")
        return False
        
    except Exception as e:
        logger.error(f"Error during EDS API logout: {str(e)}")
        return False

def get_alarm_events(
    base_url: str, 
    username: str, 
    password: str, 
    since_timestamp: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Get alarm events from the EDS API.
    
    Args:
        base_url: Base URL of the EDS API
        username: EDS API username
        password: EDS API password
        since_timestamp: Get alarms after this timestamp
        
    Returns:
        List of alarm events
        
    Raises:
        EDSApiError: If events retrieval fails
    """
    try:
        # Make sure base_url is properly formatted
        if base_url and not base_url.startswith(('http://', 'https://')):
            base_url = f"https://{base_url}"
            
        # Authenticate first
        session_id = login(base_url, username, password)
        
        # Prepare request to fetch events
        url = f"{base_url}/api/v1/events/read"
        headers = {
            "Authorization": f"Bearer {session_id}",
            "Content-Type": "application/json"
        }
        
        # Prepare payload with filters
        payload = {
            "filters": []
        }
        
        # Add timestamp filter if provided
        if since_timestamp:
            timestamp_unix = int(since_timestamp.timestamp())
            logger.info(f"Checking for alarms since timestamp: {since_timestamp} (Unix: {timestamp_unix})")
            payload["filters"].append({
                "ts": {
                    "from": timestamp_unix
                }
            })
        else:
            logger.info("No timestamp filter provided, retrieving all events")
        
        # Request events
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        
        if response.status_code != 200:
            logger.error(f"EDS API events retrieval failed: {response.status_code} - {response.text}")
            raise EDSApiError(f"Events retrieval failed with status code {response.status_code}")
        
        try:
            data = response.json()
            events = data.get('events', [])
            
            logger.info(f"Received {len(events)} events from EDS API")
            
            # Process events to extract alarm information
            alarm_events = []
            for event in events:
                # Look for alarm events only
                if 'alarm' in event.get('type', '').lower() or event.get('priority', '').upper() in ['HIGH', 'CRITICAL']:
                    alarm_event = {
                        'id': event.get('id', ''),
                        'description': event.get('description', 'Unknown alarm'),
                        'source': event.get('source', 'Unknown'),
                        'timestamp': datetime.fromtimestamp(event.get('timestamp', 0)),
                        'severity': event.get('priority', 'MEDIUM').upper(),
                        'status': event.get('status', 'ACTIVE').upper(),
                        'raw_data': event
                    }
                    alarm_events.append(alarm_event)
            
            logger.info(f"Extracted {len(alarm_events)} alarm events from response")
            
            # Clean up the session
            logout(base_url, session_id)
            
            return alarm_events
            
        except json.JSONDecodeError as e:
            logger.error(f"EDS API JSON decode error for events: {str(e)}")
            raise EDSApiError(f"JSON decode error: {str(e)}")
        
        
    except EDSApiError:
        raise
    except requests.RequestException as e:
        logger.error(f"EDS API request error during events retrieval: {str(e)}")
        raise EDSApiError(f"Request error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during EDS API events retrieval: {str(e)}")
        raise EDSApiError(f"Unexpected error: {str(e)}")
