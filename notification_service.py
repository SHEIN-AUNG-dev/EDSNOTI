import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Configure logging
logger = logging.getLogger(__name__)

class TwilioError(Exception):
    """Exception raised for errors in Twilio SMS service."""
    pass

def check_connection(account_sid: str, auth_token: str) -> bool:
    """
    Check if we can connect to the Twilio API.
    
    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        client = Client(account_sid, auth_token)
        # Try to fetch account info - this will fail if credentials are wrong
        client.api.accounts(account_sid).fetch()
        return True
    except TwilioRestException as e:
        logger.error(f"Twilio connection check failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking Twilio connection: {str(e)}")
        return False

def send_sms(account_sid: str, auth_token: str, from_number: str, to_number: str, message: str) -> str:
    """
    Send an SMS message using Twilio.
    
    Args:
        account_sid: Twilio account SID
        auth_token: Twilio auth token
        from_number: Twilio phone number to send from
        to_number: Recipient's phone number
        message: Message content
        
    Returns:
        Message SID if successful
        
    Raises:
        TwilioError: If SMS sending fails
    """
    try:
        client = Client(account_sid, auth_token)
        
        # Sanitize phone numbers if needed
        if not to_number.startswith('+'):
            to_number = f"+{to_number}"
            
        if not from_number.startswith('+'):
            from_number = f"+{from_number}"
        
        # Send the message
        twilio_message = client.messages.create(
            body=message,
            from_=from_number,
            to=to_number
        )
        
        logger.info(f"SMS sent successfully to {to_number}, SID: {twilio_message.sid}")
        return twilio_message.sid
        
    except TwilioRestException as e:
        logger.error(f"Twilio error sending SMS: {str(e)}")
        raise TwilioError(f"Twilio API error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error sending SMS: {str(e)}")
        raise TwilioError(f"Unexpected error: {str(e)}")
