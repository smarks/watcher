#!/usr/bin/env python3
"""
ClickSend SMS Setup and Troubleshooting Script
This script helps diagnose issues with ClickSend SMS configuration and API calls
"""

import logging
import os
import sys
from datetime import datetime

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set"""
    logger.info("=== CHECKING ENVIRONMENT VARIABLES ===")

    required_vars = ["SMS_PHONE_NUMBER", "CLICKSEND_USERNAME", "CLICKSEND_API_KEY"]

    optional_vars = ["CLICKSEND_SOURCE"]

    all_good = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(
                f"✓ {var}: {'*' * len(value[:-4]) + value[-4:] if len(value) > 4 else '***'}"
            )
        else:
            logger.error(f"✗ {var}: NOT SET")
            all_good = False

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✓ {var}: {value}")
        else:
            logger.info(f"- {var}: Not set (using default)")

    return all_good


def check_clicksend_library():
    """Check if ClickSend library is installed and importable"""
    logger.info("\n=== CHECKING CLICKSEND LIBRARY ===")

    try:
        import clicksend_client
        from clicksend_client import SmsMessage, SmsMessageCollection  # noqa: F401
        from clicksend_client.rest import ApiException  # noqa: F401

        logger.info("✓ clicksend_client library is installed and importable")
        logger.info(f"✓ Library version: {getattr(clicksend_client, '__version__', 'unknown')}")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import clicksend_client: {e}")
        logger.error("Install with: pip install clicksend-client")
        return False


def integration_test_clicksend_connection():
    """Test the ClickSend API connection and authentication"""
    logger.info("\n=== TESTING CLICKSEND API CONNECTION ===")

    try:
        import clicksend_client
        from clicksend_client import SmsMessage, SmsMessageCollection
        from clicksend_client.rest import ApiException

        username = os.getenv("CLICKSEND_USERNAME")
        api_key = os.getenv("CLICKSEND_API_KEY")
        phone_number = os.getenv("SMS_PHONE_NUMBER")
        source = os.getenv("CLICKSEND_SOURCE", "URLWatcher")

        # Configure API client
        configuration = clicksend_client.Configuration()
        configuration.username = username
        configuration.password = api_key

        logger.info(f"Connecting to ClickSend API with username: {username}")
        api_instance = clicksend_client.SMSApi(clicksend_client.ApiClient(configuration))

        # Test with account info first (if available)
        try:
            account_api = clicksend_client.AccountApi(clicksend_client.ApiClient(configuration))
            account_info = account_api.account_get()
            logger.info("✓ API authentication successful")
            logger.info(f"Account info: {account_info}")
        except Exception as e:
            logger.warning(f"Could not get account info (but may still work for SMS): {e}")

        # Create a test SMS message
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        test_message = f"ClickSend test from URL Watcher at {timestamp}"

        logger.info(f"Creating test SMS to: {phone_number}")
        logger.info(f"From: {source}")
        logger.info(f"Message: {test_message}")

        sms_message = SmsMessage(source=source, body=test_message, to=phone_number)

        sms_messages = SmsMessageCollection(messages=[sms_message])

        logger.info("Sending test SMS...")

        # Send the message
        api_response = api_instance.sms_send_post(sms_messages)

        logger.info("Raw API response:")
        logger.info(f"Response object: {api_response}")
        logger.info(f"Response type: {type(api_response)}")

        # Detailed response analysis
        if api_response:
            logger.info(f"Has 'data' attribute: {hasattr(api_response, 'data')}")

            if hasattr(api_response, "data"):
                data = api_response.data
                logger.info(f"Data object: {data}")
                logger.info(f"Data type: {type(data)}")
                logger.info(f"Has 'messages' attribute: {hasattr(data, 'messages')}")

                if hasattr(data, "messages") and data.messages:
                    for i, message_data in enumerate(data.messages):
                        logger.info(f"Message {i+1}:")
                        logger.info(f"  Type: {type(message_data)}")
                        logger.info(f"  Has 'status': {hasattr(message_data, 'status')}")
                        logger.info(f"  Has 'message_id': {hasattr(message_data, 'message_id')}")
                        logger.info(f"  Has 'to': {hasattr(message_data, 'to')}")
                        logger.info(f"  Has 'body': {hasattr(message_data, 'body')}")

                        if hasattr(message_data, "status"):
                            status = message_data.status
                            logger.info(f"  Status: {status}")

                            if status == "SUCCESS":
                                logger.info("✓ SMS sent successfully!")
                                if hasattr(message_data, "message_id"):
                                    logger.info(f"  Message ID: {message_data.message_id}")
                            else:
                                logger.error(f"✗ SMS failed with status: {status}")

                                # Log additional error details
                                for attr in dir(message_data):
                                    if not attr.startswith("_") and attr not in [
                                        "status",
                                        "message_id",
                                    ]:
                                        try:
                                            value = getattr(message_data, attr)
                                            if not callable(value):
                                                logger.error(f"  {attr}: {value}")
                                        except Exception:
                                            pass
                        else:
                            logger.error("  No status information available")
                else:
                    logger.error("✗ No messages in response")
            else:
                logger.error("✗ No data in API response")
        else:
            logger.error("✗ No API response received")

        return True

    except ApiException as e:
        logger.error(f"✗ ClickSend API Exception: {e}")
        logger.error(f"Status code: {e.status}")
        logger.error(f"Reason: {e.reason}")
        logger.error(f"Body: {e.body}")
        return False

    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return False


def integration_test_our_notifier():
    """Test our ClickSend notifier implementation"""
    logger.info("\n=== TESTING OUR CLICKSEND NOTIFIER ===")

    try:
        from clicksend_sms_notifier import create_notifier_from_env

        # from clicksend_sms_notifier import ClickSendSMSNotifier  # noqa: F401

        logger.info("Creating notifier from environment...")
        notifier = create_notifier_from_env()

        logger.info(f"Notifier configured: {notifier.is_configured()}")
        logger.info(f"Phone number: {notifier.phone_number}")
        logger.info(f"Username: {notifier.username}")
        api_key_display = (
            "***" + notifier.api_key[-4:]
            if notifier.api_key and len(notifier.api_key) > 4
            else "***"
        )
        logger.info(f"API key: {api_key_display}")
        logger.info(f"Source: {notifier.source}")

        if notifier.is_configured():
            logger.info("Running test notification...")
            result = notifier.test_notification()

            logger.info(f"Test result: {result}")

            if result.get("success"):
                logger.info("✓ Our notifier test passed!")
            else:
                logger.error(f"✗ Our notifier test failed: {result.get('error', 'Unknown error')}")
        else:
            logger.error("✗ Notifier not properly configured")

    except ImportError as e:
        logger.error(f"✗ Could not import our notifier: {e}")
    except Exception as e:
        logger.error(f"✗ Error testing our notifier: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")


def main():
    """Run all diagnostic tests"""
    logger.info("ClickSend SMS Troubleshooting Script")
    logger.info("=" * 50)

    # Check environment
    env_ok = check_environment()

    # Check library
    lib_ok = check_clicksend_library()

    if not env_ok:
        logger.error("\n❌ Environment variables not properly configured!")
        logger.error("Please set the required environment variables in your .env file")
        return False

    if not lib_ok:
        logger.error("\n❌ ClickSend library not available!")
        logger.error("Please install with: pip install clicksend-client")
        return False

    # Test API connection
    api_ok = integration_test_clicksend_connection()

    # Test our notifier
    integration_test_our_notifier()

    if api_ok:
        logger.info("\n✅ All tests completed successfully!")
    else:
        logger.error("\n❌ Some tests failed. Check the logs above for details.")

    return api_ok


if __name__ == "__main__":
    main()
