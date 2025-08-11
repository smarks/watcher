#!/usr/bin/env python3
"""
Twilio SMS notification system for URL Watcher

This module provides SMS notification functionality using Twilio's API
as an alternative to AWS SNS.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional, Any

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    Client = None
    TwilioException = Exception

# Configure logging
logger = logging.getLogger(__name__)


class TwilioNotifier:
    """
    Handles SMS notifications using Twilio API
    
    This class provides a simple interface for sending SMS notifications
    when URL content changes are detected.
    """

    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        from_phone: Optional[str] = None,
        to_phone: Optional[str] = None,
    ):
        """
        Initialize the Twilio SMS notifier
        
        Args:
            account_sid (str, optional): Twilio Account SID
            auth_token (str, optional): Twilio Auth Token  
            from_phone (str, optional): Twilio phone number (sender)
            to_phone (str, optional): Recipient phone number
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_phone = from_phone
        self.to_phone = to_phone
        self.client = None
        
        if not TWILIO_AVAILABLE:
            logger.warning("Twilio package not installed. Install with: pip install twilio")
            return
            
        # Initialize Twilio client if credentials provided
        if self.account_sid and self.auth_token:
            try:
                self.client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Twilio client: {e}")
                self.client = None

    def is_configured(self) -> bool:
        """
        Check if Twilio notifications are properly configured
        
        Returns:
            bool: True if configured and ready to send SMS, False otherwise
        """
        if not TWILIO_AVAILABLE:
            return False
            
        return (
            self.client is not None
            and self.account_sid is not None
            and self.auth_token is not None
            and self.from_phone is not None
            and self.to_phone is not None
        )

    def send_notification(
        self, url: str, message: str, subject: Optional[str] = None
    ) -> bool:
        """
        Send SMS notification about URL change
        
        Args:
            url (str): The URL that changed
            message (str): The change description/diff
            subject (str, optional): Message subject (not used in SMS)
            
        Returns:
            bool: True if SMS sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.warning("Twilio notifier not configured - cannot send SMS")
            return False

        try:
            # Format SMS message
            sms_body = self._format_message(url, message, subject)
            
            # Send SMS via Twilio
            message = self.client.messages.create(
                body=sms_body,
                from_=self.from_phone,
                to=self.to_phone
            )
            
            logger.info(f"SMS sent successfully - Message SID: {message.sid}")
            return True
            
        except TwilioException as e:
            logger.error(f"Twilio API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send SMS notification: {e}")
            return False

    def _format_message(self, url: str, content: str, subject: Optional[str] = None) -> str:
        """
        Format the SMS message content
        
        Args:
            url (str): The URL that changed
            content (str): The change description
            subject (str, optional): Message subject
            
        Returns:
            str: Formatted SMS message
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Twilio SMS has 1600 character limit, so we need to truncate
        max_content_length = 1200  # Leave room for other text
        
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        message_parts = [
            "🚨 URL CHANGE DETECTED",
            f"Time: {timestamp}",
            f"URL: {url}",
            "",
            "Changes detected:",
            content,
            "",
            "Powered by URL Watcher + Twilio"
        ]
        
        return "\n".join(message_parts)

    def test_notification(self) -> Dict[str, Any]:
        """
        Send a test SMS to verify configuration
        
        Returns:
            dict: Test results with success status and details
        """
        if not TWILIO_AVAILABLE:
            return {
                "success": False,
                "message": "Twilio package not installed",
                "error": "Install with: pip install twilio"
            }
            
        if not self.is_configured():
            missing = []
            if not self.account_sid:
                missing.append("account_sid")
            if not self.auth_token:
                missing.append("auth_token")
            if not self.from_phone:
                missing.append("from_phone")
            if not self.to_phone:
                missing.append("to_phone")
                
            return {
                "success": False,
                "message": "Twilio not configured",
                "error": f"Missing: {', '.join(missing)}"
            }

        try:
            # Send test message
            test_message = (
                "✅ URL Watcher Test Message\n\n"
                f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                "If you receive this, Twilio SMS is working correctly!\n\n"
                "Powered by URL Watcher + Twilio"
            )
            
            message = self.client.messages.create(
                body=test_message,
                from_=self.from_phone,
                to=self.to_phone
            )
            
            return {
                "success": True,
                "message": "Test SMS sent successfully",
                "message_id": message.sid,
                "status": message.status
            }
            
        except TwilioException as e:
            return {
                "success": False,
                "message": "Twilio API error",
                "error": str(e)
            }
        except Exception as e:
            return {
                "success": False,
                "message": "Failed to send test SMS",
                "error": str(e)
            }


def create_notifier_from_env() -> TwilioNotifier:
    """
    Create a TwilioNotifier using environment variables
    
    Expected environment variables:
    - TWILIO_ACCOUNT_SID: Your Twilio Account SID
    - TWILIO_AUTH_TOKEN: Your Twilio Auth Token
    - TWILIO_FROM_PHONE: Your Twilio phone number (e.g., +1234567890)
    - TWILIO_TO_PHONE: Recipient phone number (e.g., +1987654321)
    
    Returns:
        TwilioNotifier: Configured SMS notifier instance
    """
    return TwilioNotifier(
        account_sid=os.environ.get("TWILIO_ACCOUNT_SID"),
        auth_token=os.environ.get("TWILIO_AUTH_TOKEN"),
        from_phone=os.environ.get("TWILIO_FROM_PHONE"),
        to_phone=os.environ.get("TWILIO_TO_PHONE"),
    )


# For backward compatibility, also provide AWS-style function name
def create_twilio_notifier_from_env() -> TwilioNotifier:
    """Alias for create_notifier_from_env() for clarity"""
    return create_notifier_from_env()


if __name__ == "__main__":
    # Quick test when run directly
    print("🔍 Testing Twilio SMS Notifier...")
    
    notifier = create_notifier_from_env()
    
    if not notifier.is_configured():
        print("❌ Twilio not configured. Set these environment variables:")
        print("   export TWILIO_ACCOUNT_SID='your_account_sid'")
        print("   export TWILIO_AUTH_TOKEN='your_auth_token'")
        print("   export TWILIO_FROM_PHONE='+1234567890'")
        print("   export TWILIO_TO_PHONE='+1987654321'")
    else:
        print("✅ Twilio configured! Sending test message...")
        result = notifier.test_notification()
        
        if result["success"]:
            print(f"✅ Test SMS sent! Message ID: {result['message_id']}")
        else:
            print(f"❌ Test failed: {result['message']}")
            if "error" in result:
                print(f"   Error: {result['error']}")