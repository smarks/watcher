#!/usr/bin/env python3
"""
ClickSend SMS Notification Module for URL Watcher
Sends SMS notifications via ClickSend API when URL changes are detected
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

try:
    import clicksend_client
    from clicksend_client import SmsMessage, SmsMessageCollection
    from clicksend_client.rest import ApiException

    CLICKSEND_AVAILABLE = True
except ImportError:
    CLICKSEND_AVAILABLE = False
    logging.warning("clicksend_client not installed. Install with: pip install clicksend-client")


class ClickSendSMSNotifier:
    """Handles SMS notifications via ClickSend API"""

    def __init__(
        self,
        phone_number: Optional[str] = None,
        username: Optional[str] = None,
        api_key: Optional[str] = None,
        source: Optional[str] = None,
    ):
        """
        Initialize ClickSend SMS notifier

        Args:
            phone_number: Phone number to send SMS to (e.g., "+1234567890")
            username: ClickSend username
            api_key: ClickSend API key
            source: Source name for SMS (e.g., "URLWatcher")
        """
        self.phone_number = phone_number or os.getenv("SMS_PHONE_NUMBER")
        self.username = username or os.getenv("CLICKSEND_USERNAME")
        self.api_key = api_key or os.getenv("CLICKSEND_API_KEY")
        self.source = source or os.getenv("CLICKSEND_SOURCE", "URLWatcher")

        # Initialize API client if credentials are provided
        self.api_instance = None
        if self.is_configured() and CLICKSEND_AVAILABLE:
            self._initialize_client()

    def _initialize_client(self):
        """Initialize the ClickSend API client"""
        configuration = clicksend_client.Configuration()
        configuration.username = self.username
        configuration.password = self.api_key
        self.api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))

    def is_configured(self) -> bool:
        """Check if SMS notifications are properly configured"""
        return (
            self.phone_number is not None
            and self.username is not None
            and self.api_key is not None
            and CLICKSEND_AVAILABLE
        )

    def send_notification(self, url: str, message: str, subject: Optional[str] = None) -> bool:
        """
        Send SMS notification about URL change

        Args:
            url: The URL that changed
            message: Change description/diff
            subject: Optional subject line (included in message)

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.is_configured():
            logging.warning("ClickSend SMS notifications not configured - skipping")
            return False

        if not self.api_instance:
            logging.error("ClickSend API client not initialized")
            return False

        # Log SMS attempt start
        logging.info(f"[SMS] Attempting to send SMS via ClickSend to {self.phone_number}")
        logging.info(f"[SMS] URL being monitored: {url}")
        logging.info(f"[SMS] Source: {self.source}")

        try:
            # Prepare message with the actual URL that changed
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sms_body = "WEBSITE CHANGE DETECTED\n"
            sms_body += f"Time: {timestamp}\n"
            # sms_body += f"URL: {url}\n\n"

            # Include diff if provided, but limit length for SMS (160-1600 chars typical limit)
            if message and message.strip():
                # Truncate diff to fit in SMS (leaving room for header)
                max_diff_length = 500  # Conservative limit
                if len(message) > max_diff_length:
                    truncated_diff = message[:max_diff_length] + "...\n[truncated]"
                    sms_body += "Changes:\n" + truncated_diff
                else:
                    sms_body += "Changes:\n" + message
            else:
                sms_body += "Content changes detected."

            # Log the message being sent
            logging.info(f"[SMS] Message content: {repr(sms_body)}")

            # Create SMS message
            sms_message = SmsMessage(source=self.source, body=sms_body, to=self.phone_number)

            sms_messages = SmsMessageCollection(messages=[sms_message])

            # Send message via ClickSend API
            logging.debug("[SMS] Sending POST request to ClickSend API...")
            api_response = self.api_instance.sms_send_post(sms_messages)
            logging.debug(f"[SMS] Raw API response: {api_response}")
            logging.debug(f"[SMS] Response type: {type(api_response)}")

            # Handle both dict, string, and object responses from ClickSend API
            response_data = None
            if isinstance(api_response, str):
                # Parse string response (could be JSON or Python dict string)
                import ast
                import json

                try:
                    # First try JSON parsing
                    parsed_response = json.loads(api_response)
                    response_data = parsed_response.get("data")
                except json.JSONDecodeError:
                    try:
                        # Try parsing as Python dict literal
                        parsed_response = ast.literal_eval(api_response)
                        response_data = parsed_response.get("data")
                    except (ValueError, SyntaxError):
                        logging.error(f"Failed to parse API response: {api_response}")
            elif isinstance(api_response, dict):
                response_data = api_response.get("data")
            elif api_response and hasattr(api_response, "data"):
                response_data = api_response.data

            # Check if message was sent successfully
            if response_data:
                logging.debug(f"Response data: {response_data}")
                logging.debug(f"Data type: {type(response_data)}")

                messages = None
                if isinstance(response_data, dict):
                    messages = response_data.get("messages")
                elif hasattr(response_data, "messages"):
                    messages = response_data.messages

                logging.debug(f"Messages: {messages}")

                if messages:
                    logging.debug(f"Number of messages: {len(messages)}")
                    message_data = messages[0]
                    logging.debug(f"Message data: {message_data}")
                    logging.debug(f"Message data type: {type(message_data)}")

                    # Handle both dict and object message data
                    status = None
                    message_id = None

                    if isinstance(message_data, dict):
                        status = message_data.get("status")
                        message_id = message_data.get("message_id")
                    else:
                        status = getattr(message_data, "status", None)
                        message_id = getattr(message_data, "message_id", None)

                    logging.debug(f"Status: {status}, Message ID: {message_id}")

                    if status == "SUCCESS":
                        logging.info("[SMS] ✓ SMS sent successfully via ClickSend")
                        logging.info(f"[SMS] Message ID: {message_id}")
                        logging.info(f"[SMS] Recipient: {self.phone_number}")
                        logging.info(f"[SMS] Source: {self.source}")
                        return True
                    else:
                        logging.error("[SMS] ✗ Failed to send SMS via ClickSend")
                        logging.error(f"[SMS] Message status: {status}")
                        logging.error(f"[SMS] Recipient: {self.phone_number}")
                        logging.error(f"[SMS] Source: {self.source}")

                        # Log additional error details for dict responses
                        if isinstance(message_data, dict):
                            for key in [
                                "error_text",
                                "error_code",
                                "from",
                                "to",
                                "body",
                            ]:
                                if key in message_data:
                                    logging.error(f"[SMS]   {key}: {message_data[key]}")

                        return False
                else:
                    logging.error("[SMS] ✗ Failed to send SMS via ClickSend")
                    logging.error("[SMS] Error: No messages in response data")
                    logging.error(f"[SMS] Recipient: {self.phone_number}")
                    return False

            logging.error("[SMS] ✗ Failed to send SMS via ClickSend")
            logging.error("[SMS] Error: Invalid response structure or no data")
            logging.error(f"[SMS] API response: {api_response}")
            logging.error(f"[SMS] Recipient: {self.phone_number}")
            return False

        except ApiException as e:
            logging.error("[SMS] ✗ Failed to send SMS via ClickSend - API exception")
            logging.error(f"[SMS] Error details: {e}")
            logging.error(f"[SMS] Recipient: {self.phone_number}")
            logging.error(f"[SMS] Source: {self.source}")
            return False

        except Exception as e:
            logging.error("[SMS] ✗ Failed to send SMS via ClickSend - Unexpected error")
            logging.error(f"[SMS] Error details: {e}")
            logging.error(f"[SMS] Recipient: {self.phone_number}")
            logging.error(f"[SMS] Source: {self.source}")
            return False

    def test_notification(self) -> Dict[str, Any]:
        """
        Send a test notification to verify configuration

        Returns:
            dict: Test results with status and details
        """
        if not CLICKSEND_AVAILABLE:
            logging.warning("[SMS TEST] ClickSend library not installed")
            return {
                "success": False,
                "error": "clicksend_client library not installed",
                "details": {"install_command": "pip install clicksend-client"},
            }

        if not self.is_configured():
            logging.warning("[SMS TEST] ClickSend SMS notifications not configured")
            return {
                "success": False,
                "error": "ClickSend SMS notifications not configured",
                "details": {
                    "phone_number": self.phone_number is not None,
                    "username": self.username is not None,
                    "api_key": self.api_key is not None,
                    "source": self.source,
                    "library_available": CLICKSEND_AVAILABLE,
                },
            }

        if not self.api_instance:
            logging.error("[SMS TEST] ClickSend API client not initialized")
            return {
                "success": False,
                "error": "ClickSend API client not initialized",
            }

        logging.info(f"[SMS TEST] Attempting to send test SMS via ClickSend to {self.phone_number}")
        logging.info(f"[SMS TEST] Source: {self.source}")

        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            test_message = (
                f"Test notification from URL Watcher at {timestamp}\n"
                "This is a test message to verify SMS configuration."
            )
            logging.info(f"[SMS TEST] Test message: {repr(test_message)}")

            # Create SMS message
            sms_message = SmsMessage(source=self.source, body=test_message, to=self.phone_number)

            sms_messages = SmsMessageCollection(messages=[sms_message])

            # Send test message
            logging.debug("[SMS TEST] Sending POST request to ClickSend API...")
            api_response = self.api_instance.sms_send_post(sms_messages)
            logging.debug(f"[SMS TEST] API Response: {api_response}")

            # Handle both dict, string, and object responses from ClickSend API
            response_data = None
            if isinstance(api_response, str):
                # Parse string response (could be JSON or Python dict string)
                import ast
                import json

                try:
                    # First try JSON parsing
                    parsed_response = json.loads(api_response)
                    response_data = parsed_response.get("data")
                except json.JSONDecodeError:
                    try:
                        # Try parsing as Python dict literal
                        parsed_response = ast.literal_eval(api_response)
                        response_data = parsed_response.get("data")
                    except (ValueError, SyntaxError):
                        logging.error(f"Failed to parse API response: {api_response}")
            elif isinstance(api_response, dict):
                response_data = api_response.get("data")
            elif api_response and hasattr(api_response, "data"):
                response_data = api_response.data

            # Check if message was sent successfully
            if response_data:
                messages = None
                if isinstance(response_data, dict):
                    messages = response_data.get("messages")
                elif hasattr(response_data, "messages"):
                    messages = response_data.messages

                if messages:
                    message_data = messages[0]

                    # Handle both dict and object message data
                    status = None
                    message_id = None

                    if isinstance(message_data, dict):
                        status = message_data.get("status")
                        message_id = message_data.get("message_id")
                    else:
                        status = getattr(message_data, "status", None)
                        message_id = getattr(message_data, "message_id", None)

                    if status == "SUCCESS":
                        logging.info("[SMS TEST] ✓ Test SMS sent successfully via ClickSend")
                        logging.info(f"[SMS TEST] Message ID: {message_id}")
                        return {
                            "success": True,
                            "message_id": message_id,
                            "details": {
                                "phone_number": self.phone_number,
                                "source": self.source,
                            },
                        }
                    else:
                        logging.error("[SMS TEST] ✗ Test SMS failed via ClickSend")
                        logging.error(f"[SMS TEST] Message status: {status}")
                        return {
                            "success": False,
                            "error": f"ClickSend API error: Message status: {status}",
                        }
                else:
                    logging.error("[SMS TEST] ✗ Test SMS failed via ClickSend")
                    logging.error("[SMS TEST] Error: No messages in response")
                    return {
                        "success": False,
                        "error": "ClickSend API error: No messages in response",
                    }

            logging.error("[SMS TEST] ✗ Test SMS failed via ClickSend")
            logging.error("[SMS TEST] Error: Invalid response structure")
            return {
                "success": False,
                "error": "ClickSend API error: Invalid response structure",
            }

        except ApiException as e:
            logging.error(f"[SMS TEST] ✗ Test SMS failed via ClickSend - API exception: {str(e)}")
            return {"success": False, "error": f"ClickSend API exception: {str(e)}"}

        except Exception as e:
            logging.error(
                f"[SMS TEST] ✗ Test SMS failed via ClickSend - Unexpected error: {str(e)}"
            )
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


def create_notifier_from_env(load_dotenv: bool = True) -> ClickSendSMSNotifier:
    """
    Create ClickSend SMS notifier using environment variables

    Expected environment variables:
    - SMS_PHONE_NUMBER: Phone number to send SMS to (e.g., "+1234567890")
    - CLICKSEND_USERNAME: ClickSend username
    - CLICKSEND_API_KEY: ClickSend API key
    - CLICKSEND_SOURCE: Source name for SMS (optional, default: "URLWatcher")

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

    return ClickSendSMSNotifier(
        phone_number=os.getenv("SMS_PHONE_NUMBER"),
        username=os.getenv("CLICKSEND_USERNAME"),
        api_key=os.getenv("CLICKSEND_API_KEY"),
        source=os.getenv("CLICKSEND_SOURCE", "URLWatcher"),
    )
