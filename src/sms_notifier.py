#!/usr/bin/env python3
"""
SMS Notification Module for URL Watcher
Sends SMS notifications via TextBelt API when URL changes are detected
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import requests


class SMSNotifier:
    """Handles SMS notifications via TextBelt API"""

    def __init__(
        self,
        phone_number: Optional[str] = None,
        api_key: Optional[str] = None,
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

    def send_notification(self, url: str, message: str, subject: Optional[str] = None) -> bool:
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

        # Log SMS attempt start
        logging.info(f"[SMS] Attempting to send SMS via TextBelt to {self.phone_number}")
        logging.info(f"[SMS] URL being monitored: {url}")

        try:
            # Prepare message with the actual URL that changed
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sms_message = "WEBSITE CHANGE DETECTED\n"
            sms_message += f"Time: {timestamp}\n"
            sms_message += f"URL: {url}\n\n"

            # Include diff if provided, but limit length for SMS (160-1600 chars typical limit)
            if message and message.strip():
                # Truncate diff to fit in SMS (leaving room for header)
                max_diff_length = 500  # Conservative limit
                if len(message) > max_diff_length:
                    truncated_diff = message[:max_diff_length] + "...\n[truncated]"
                    sms_message += "Changes:\n" + truncated_diff
                else:
                    sms_message += "Changes:\n" + message
            else:
                sms_message += "Content changes detected."

            # Log the message being sent
            logging.info(f"[SMS] Message content: {repr(sms_message)}")
            logging.debug(f"[SMS] API URL: {self.api_url}")

            # Send message via TextBelt API
            payload = {
                "phone": self.phone_number,
                "message": sms_message,
                "key": self.api_key,
            }

            logging.debug("[SMS] Sending POST request to TextBelt API...")
            response = requests.post(self.api_url, data=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            logging.debug(f"[SMS] API Response: {result}")

            if result.get("success"):
                text_id = result.get("textId")
                logging.info("[SMS] ✓ SMS sent successfully via TextBelt")
                logging.info(f"[SMS] TextId: {text_id}")
                logging.info(f"[SMS] Recipient: {self.phone_number}")
                return True
            else:
                error_msg = result.get("error", "Unknown error")
                logging.error("[SMS] ✗ Failed to send SMS via TextBelt")
                logging.error(f"[SMS] Error: {error_msg}")
                logging.error(f"[SMS] Recipient: {self.phone_number}")
                return False

        except requests.exceptions.RequestException as e:
            logging.error("[SMS] ✗ Failed to send SMS - HTTP error")
            logging.error(f"[SMS] Error details: {e}")
            logging.error(f"[SMS] Recipient: {self.phone_number}")
            return False

        except Exception as e:
            logging.error("[SMS] ✗ Failed to send SMS - Unexpected error")
            logging.error(f"[SMS] Error details: {e}")
            logging.error(f"[SMS] Recipient: {self.phone_number}")
            return False

    def test_notification(self) -> Dict[str, Any]:
        """
        Send a test notification to verify configuration

        Returns:
            dict: Test results with status and details
        """
        if not self.is_configured():
            logging.warning("[SMS TEST] SMS notifications not configured")
            return {
                "success": False,
                "error": "SMS notifications not configured",
                "details": {
                    "phone_number": self.phone_number is not None,
                    "api_key": self.api_key is not None,
                },
            }

        logging.info(f"[SMS TEST] Attempting to send test SMS via TextBelt to {self.phone_number}")

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            test_message = (
                f"Test notification from URL Watcher at {timestamp}\n"
                "This is a test message to verify SMS configuration."
            )
            logging.info(f"[SMS TEST] Test message: {repr(test_message)}")

            payload = {
                "phone": self.phone_number,
                "message": test_message,
                "key": self.api_key,
            }

            logging.debug("[SMS TEST] Sending POST request to TextBelt API...")
            response = requests.post(self.api_url, data=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            logging.debug(f"[SMS TEST] API Response: {result}")

            if result.get("success"):
                text_id = result.get("textId")
                logging.info("[SMS TEST] ✓ Test SMS sent successfully")
                logging.info(f"[SMS TEST] TextId: {text_id}")
                return {
                    "success": True,
                    "text_id": text_id,
                    "details": {
                        "phone_number": self.phone_number,
                        "api_url": self.api_url,
                    },
                }
            else:
                error_msg = result.get("error", "Unknown error")
                logging.error("[SMS TEST] ✗ Test SMS failed")
                logging.error(f"[SMS TEST] Error: {error_msg}")
                return {
                    "success": False,
                    "error": f"TextBelt API error: {error_msg}",
                }

        except requests.exceptions.RequestException as e:
            logging.error(f"[SMS TEST] ✗ Test SMS failed - HTTP error: {str(e)}")
            return {"success": False, "error": f"HTTP error: {str(e)}"}

        except Exception as e:
            logging.error(f"[SMS TEST] ✗ Test SMS failed - Unexpected error: {str(e)}")
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
                            # Only set if not already in environment
                            # (allows test override)
                            if key.strip() not in os.environ:
                                os.environ[key.strip()] = value.strip()
            except Exception as e:
                logging.warning(f"Failed to load .env file: {e}")

    return SMSNotifier(
        phone_number=os.getenv("SMS_PHONE_NUMBER"),
        api_key=os.getenv("TEXTBELT_API_KEY"),
    )
