#!/usr/bin/env python3
"""
Unit tests for ClickSend SMS notification module
"""

import os
import unittest
from unittest.mock import Mock, patch

from clicksend_sms_notifier import (
    CLICKSEND_AVAILABLE,
    ClickSendSMSNotifier,
    create_notifier_from_env,
)


class TestClickSendSMSNotifier(unittest.TestCase):
    """Test cases for ClickSend SMS Notifier class"""

    def setUp(self):
        """Set up test fixtures"""
        # Clean environment variables
        for key in [
            "SMS_PHONE_NUMBER",
            "CLICKSEND_USERNAME",
            "CLICKSEND_API_KEY",
            "CLICKSEND_SOURCE",
        ]:
            if key in os.environ:
                del os.environ[key]

        # Create a configured notifier
        self.notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
            source="TestSource",
        )

    def test_initialization_with_params(self):
        """Test initialization with direct parameters"""
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_key",
            source="TestSender",
        )
        self.assertEqual(notifier.phone_number, "+1234567890")
        self.assertEqual(notifier.username, "test_user")
        self.assertEqual(notifier.api_key, "test_key")
        self.assertEqual(notifier.source, "TestSender")

    def test_initialization_from_env(self):
        """Test initialization from environment variables"""
        os.environ["SMS_PHONE_NUMBER"] = "+9876543210"
        os.environ["CLICKSEND_USERNAME"] = "env_user"
        os.environ["CLICKSEND_API_KEY"] = "env_key"
        os.environ["CLICKSEND_SOURCE"] = "EnvSource"

        notifier = ClickSendSMSNotifier()
        self.assertEqual(notifier.phone_number, "+9876543210")
        self.assertEqual(notifier.username, "env_user")
        self.assertEqual(notifier.api_key, "env_key")
        self.assertEqual(notifier.source, "EnvSource")

    @unittest.skipUnless(CLICKSEND_AVAILABLE, "clicksend_client not installed")
    def test_is_configured_true(self):
        """Test is_configured returns True when properly configured"""
        self.assertTrue(self.notifier.is_configured())

    def test_is_configured_false_missing_phone(self):
        """Test is_configured returns False when phone number is missing"""
        notifier = ClickSendSMSNotifier(username="user", api_key="key")
        self.assertFalse(notifier.is_configured())

    def test_is_configured_false_missing_username(self):
        """Test is_configured returns False when username is missing"""
        notifier = ClickSendSMSNotifier(phone_number="+1234567890", api_key="key")
        self.assertFalse(notifier.is_configured())

    def test_is_configured_false_missing_api_key(self):
        """Test is_configured returns False when API key is missing"""
        notifier = ClickSendSMSNotifier(phone_number="+1234567890", username="user")
        self.assertFalse(notifier.is_configured())

    @unittest.skipUnless(CLICKSEND_AVAILABLE, "clicksend_client not installed")
    @patch("clicksend_sms_notifier.clicksend_client.SMSApi")
    def test_send_notification_success(self, mock_sms_api_class):
        """Test successful SMS notification"""
        # Create mock response structure
        mock_message = Mock()
        mock_message.status = "SUCCESS"
        mock_message.message_id = "msg_123456"

        mock_data = Mock()
        mock_data.messages = [mock_message]

        mock_response = Mock()
        mock_response.data = mock_data

        # Setup mock API instance
        mock_api_instance = Mock()
        mock_api_instance.sms_send_post.return_value = mock_response
        mock_sms_api_class.return_value = mock_api_instance

        # Reinitialize notifier to use mocked API
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
            source="TestSource",
        )
        notifier.api_instance = mock_api_instance

        result = notifier.send_notification(url="https://example.com", message="Content changed")

        self.assertTrue(result)
        mock_api_instance.sms_send_post.assert_called_once()

    @unittest.skipUnless(CLICKSEND_AVAILABLE, "clicksend_client not installed")
    @patch("clicksend_sms_notifier.clicksend_client.SMSApi")
    def test_send_notification_api_error(self, mock_sms_api_class):
        """Test handling of ClickSend API error"""
        # Create mock response with error status
        mock_message = Mock()
        mock_message.status = "FAILED"

        mock_data = Mock()
        mock_data.messages = [mock_message]

        mock_response = Mock()
        mock_response.data = mock_data

        # Setup mock API instance
        mock_api_instance = Mock()
        mock_api_instance.sms_send_post.return_value = mock_response
        mock_sms_api_class.return_value = mock_api_instance

        # Reinitialize notifier to use mocked API
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
            source="TestSource",
        )
        notifier.api_instance = mock_api_instance

        result = notifier.send_notification(url="https://example.com", message="Content changed")

        self.assertFalse(result)

    @unittest.skipUnless(CLICKSEND_AVAILABLE, "clicksend_client not installed")
    @patch("clicksend_sms_notifier.clicksend_client.SMSApi")
    def test_send_notification_api_exception(self, mock_sms_api_class):
        """Test handling of API exception"""
        from clicksend_client.rest import ApiException

        # Setup mock API instance that raises exception
        mock_api_instance = Mock()
        mock_api_instance.sms_send_post.side_effect = ApiException("API Error")
        mock_sms_api_class.return_value = mock_api_instance

        # Reinitialize notifier to use mocked API
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
            source="TestSource",
        )
        notifier.api_instance = mock_api_instance

        result = notifier.send_notification(url="https://example.com", message="Content changed")

        self.assertFalse(result)

    def test_send_notification_not_configured(self):
        """Test send_notification when not configured"""
        notifier = ClickSendSMSNotifier()  # No configuration
        result = notifier.send_notification(url="https://example.com", message="Content changed")
        self.assertFalse(result)

    @unittest.skipUnless(CLICKSEND_AVAILABLE, "clicksend_client not installed")
    @patch("clicksend_sms_notifier.clicksend_client.SMSApi")
    def test_test_notification_success(self, mock_sms_api_class):
        """Test successful test notification"""
        # Create mock response structure
        mock_message = Mock()
        mock_message.status = "SUCCESS"
        mock_message.message_id = "test_msg_123"

        mock_data = Mock()
        mock_data.messages = [mock_message]

        mock_response = Mock()
        mock_response.data = mock_data

        # Setup mock API instance
        mock_api_instance = Mock()
        mock_api_instance.sms_send_post.return_value = mock_response
        mock_sms_api_class.return_value = mock_api_instance

        # Reinitialize notifier to use mocked API
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
            source="TestSource",
        )
        notifier.api_instance = mock_api_instance

        result = notifier.test_notification()

        self.assertTrue(result["success"])
        self.assertEqual(result["message_id"], "test_msg_123")
        self.assertIn("details", result)

    @unittest.skipUnless(CLICKSEND_AVAILABLE, "clicksend_client not installed")
    @patch("clicksend_sms_notifier.clicksend_client.SMSApi")
    def test_test_notification_api_error(self, mock_sms_api_class):
        """Test test notification with API error"""
        # Create mock response with error status
        mock_message = Mock()
        mock_message.status = "INVALID_RECIPIENT"

        mock_data = Mock()
        mock_data.messages = [mock_message]

        mock_response = Mock()
        mock_response.data = mock_data

        # Setup mock API instance
        mock_api_instance = Mock()
        mock_api_instance.sms_send_post.return_value = mock_response
        mock_sms_api_class.return_value = mock_api_instance

        # Reinitialize notifier to use mocked API
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
            source="TestSource",
        )
        notifier.api_instance = mock_api_instance

        result = notifier.test_notification()

        self.assertFalse(result["success"])
        self.assertIn("INVALID_RECIPIENT", result["error"])

    def test_test_notification_not_configured(self):
        """Test test_notification when not configured"""
        notifier = ClickSendSMSNotifier()  # No configuration
        result = notifier.test_notification()

        self.assertFalse(result["success"])
        self.assertIn("not configured", result["error"])
        self.assertIn("details", result)

    @unittest.skipIf(CLICKSEND_AVAILABLE, "Test for when library is not available")
    def test_library_not_available(self):
        """Test behavior when clicksend_client is not installed"""
        notifier = ClickSendSMSNotifier(
            phone_number="+1234567890",
            username="test_user",
            api_key="test_api_key",
        )

        # Should not be configured if library is not available
        self.assertFalse(notifier.is_configured())

        # Test notification should return appropriate error
        result = notifier.test_notification()
        self.assertFalse(result["success"])
        self.assertIn("not installed", result["error"])

    def test_create_notifier_from_env_with_dotenv(self):
        """Test creating notifier from environment with .env file"""
        # Create a temporary .env file
        env_content = """SMS_PHONE_NUMBER=+1112223333
CLICKSEND_USERNAME=env_user
CLICKSEND_API_KEY=env_api_key
CLICKSEND_SOURCE=EnvWatcher
"""
        with open(".env", "w") as f:
            f.write(env_content)

        try:
            notifier = create_notifier_from_env(load_dotenv=True)
            self.assertEqual(notifier.phone_number, "+1112223333")
            self.assertEqual(notifier.username, "env_user")
            self.assertEqual(notifier.api_key, "env_api_key")
            self.assertEqual(notifier.source, "EnvWatcher")
        finally:
            # Clean up
            if os.path.exists(".env"):
                os.remove(".env")
            # Clean environment
            for key in [
                "SMS_PHONE_NUMBER",
                "CLICKSEND_USERNAME",
                "CLICKSEND_API_KEY",
                "CLICKSEND_SOURCE",
            ]:
                if key in os.environ:
                    del os.environ[key]

    def test_create_notifier_from_env_without_dotenv(self):
        """Test creating notifier from environment without loading .env"""
        os.environ["SMS_PHONE_NUMBER"] = "+5556667777"
        os.environ["CLICKSEND_USERNAME"] = "direct_user"
        os.environ["CLICKSEND_API_KEY"] = "direct_key"

        notifier = create_notifier_from_env(load_dotenv=False)
        self.assertEqual(notifier.phone_number, "+5556667777")
        self.assertEqual(notifier.username, "direct_user")
        self.assertEqual(notifier.api_key, "direct_key")
        self.assertEqual(notifier.source, "URLWatcher")  # Default


if __name__ == "__main__":
    unittest.main()
