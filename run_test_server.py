#!/usr/bin/env python3
"""
Run the mock EDS API server for testing purposes.
This allows comprehensive testing of the EDS Alarm Monitor system
without connecting to the real EDS API.
"""
import os
import logging
from mock_eds_api import app

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    # By default, use port 3000 for the mock API
    port = int(os.environ.get('MOCK_EDS_PORT', 3000))
    logger.info(f"Starting mock EDS API server on port {port}")
    
    # Print usage instructions for testing
    print(f"""
    ==================================================
    MOCK EDS API SERVER RUNNING ON PORT {port}
    ==================================================
    
    To use this mock API server with the EDS Alarm Monitor:
    
    1. Set these API credentials in the monitor settings:
       - API URL: http://localhost:{port}
       - Username: test
       - Password: test
       
    2. The mock server will generate random alarms
       and ensure at least one HIGH priority alarm
       to test notifications
       
    3. Press Ctrl+C to stop the server
    
    ==================================================
    """)
    
    # Run the server
    app.run(host='0.0.0.0', port=port, debug=True)