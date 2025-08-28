#!/usr/bin/env python3
"""
SMS Notification Module for URL Watcher
Sends SMS notifications via TextBelt API when URL changes are detected
"""

import os
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any


class SMSNotifier:
    """Handles SMS notifications via TextBelt API"""

    def __init__(
        self,
        phone_number: str = None,
        api_key: str = None,
    ):
        """
        Initialize SMS notifier

        Args:
            phone_number: Phone number to send SMS to (e.g., "+1234567890")
            api_key: TextBelt API key
        """
        self.phone_number = phone_number or os.getenv("SMS_PHONE_NUMBER")
        self.api_key = api_key or os.getenv("TEXTBELT_API_KEY")
        self.api_url = "https://textbelt.com/text"

    def is_configured(self) -> bool:
        """Check if SMS notifications are properly configured"""
        return self.phone_number is not None and self.api_key is not None

    def send_notification(self, url: str, message: str, subject: str = None) -> bool:
        """
        Send SMS notification about URL change

        Args:
            url: The URL that changed
            message: Change description/diff
            subject: Optional subject line (not used with TextBelt)

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.is_configured():
            logging.warning("SMS notifications not configured - skipping")
            return False

        try:
            # Prepare simple message without URLs or diffs to avoid TextBelt restrictions
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sms_message = f"WEBSITE CHANGE DETECTED\n"
            sms_message += f"Time: {timestamp}\n"
            
            # Extract and simplify domain from URL
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                # Further simplify domain to avoid detection
                domain_parts = domain.split('.')
                if len(domain_parts) > 1:
                    simplified = f"{domain_parts[0]} site"
                else:
                    simplified = "monitored site"
                sms_message += f"Site: {simplified}\n\n"
            except Exception:
                sms_message += f"Site: monitored website\n\n"

            # Use simple change notification instead of diff content
            sms_message += "Content changes detected. Check your monitoring dashboard for details."

            # Debug: Log the message being sent
            logging.info(f"Sending SMS message: {repr(sms_message)}")
            
            # Send message via TextBelt API
            payload = {
                "phone": self.phone_number,
                "message": sms_message,
                "key": self.api_key,
            }

            response = requests.post(self.api_url, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                text_id = result.get("textId")
                logging.info(f"SMS notification sent successfully. TextId: {text_id}")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                logging.error(f"TextBelt API error: {error_msg}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP error sending SMS: {e}")
            return False

        except Exception as e:
            logging.error(f"Unexpected error sending SMS: {e}")
            return False

    def test_notification(self) -> Dict[str, Any]:
        """
        Send a test notification to verify configuration

        Returns:
            dict: Test results with status and details
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMS notifications not configured",
                "details": {
                    "phone_number": self.phone_number is not None,
                    "api_key": self.api_key is not None,
                },
            }

        try:
            test_message = f"Test notification from URL Watcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            payload = {
                "phone": self.phone_number,
                "message": test_message,
                "key": self.api_key,
            }

            response = requests.post(self.api_url, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get("success"):
                return {
                    "success": True,
                    "text_id": result.get("textId"),
                    "details": {
                        "phone_number": self.phone_number,
                        "api_url": self.api_url,
                    },
                }
            else:
                return {
                    "success": False,
                    "error": f"TextBelt API error: {result.get('error', 'Unknown error')}",
                }

        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP error: {str(e)}"}

        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


def create_notifier_from_env(load_dotenv: bool = True) -> SMSNotifier:
    """
    Create SMS notifier using environment variables

    Expected environment variables:
    - SMS_PHONE_NUMBER: Phone number to send SMS to (e.g., "+1234567890")
    - TEXTBELT_API_KEY: TextBelt API key

    Args:
        load_dotenv: Whether to load .env file (default: True)
    """
    # Try to load .env file only if requested (for testing flexibility)
    if load_dotenv:
        env_file = ".env"
        if os.path.exists(env_file):
            try:
                with open(env_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            # Only set if not already in environment (allows test override)
                            if key.strip() not in os.environ:
                                os.environ[key.strip()] = value.strip()
            except Exception as e:
                logging.warning(f"Failed to load .env file: {e}")

    return SMSNotifier(
        phone_number=os.getenv("SMS_PHONE_NUMBER"),
        api_key=os.getenv("TEXTBELT_API_KEY"),
    )
