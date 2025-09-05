#!/usr/bin/env python3
"""
Test suite for SMS notification functionality using TextBelt API
"""

import logging
import os
import unittest
from unittest.mock import Mock, patch

import requests

from sms_notifier import SMSNotifier, create_notifier_from_env
from url_watcher import URLWatcher


class TestSMSNotifier(unittest.TestCase):
    """Test cases for SMSNotifier class using TextBelt API"""

    def setUp(self):
        """Set up test fixtures"""
        self.phone_number = "+1234567890"
        self.api_key = "test_api_key"

    def test_initialization_with_params(self):
        """Test SMSNotifier initialization with parameters"""
        notifier = SMSNotifier(
            phone_number=self.phone_number,
            api_key=self.api_key,
        )

        self.assertEqual(notifier.phone_number, self.phone_number)
        self.assertEqual(notifier.api_key, self.api_key)
        self.assertEqual(notifier.api_url, "https://textbelt.com/text")

    def test_initialization_from_env(self):
        """Test SMSNotifier initialization from environment variables"""
        with patch.dict(
            os.environ,
            {"SMS_PHONE_NUMBER": self.phone_number, "TEXTBELT_API_KEY": self.api_key},
        ):
            notifier = SMSNotifier()
            self.assertEqual(notifier.phone_number, self.phone_number)
            self.assertEqual(notifier.api_key, self.api_key)

    def test_is_configured_true(self):
        """Test is_configured returns True when properly set up"""
        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)
        self.assertTrue(notifier.is_configured())

    def test_is_configured_false_no_phone(self):
        """Test is_configured returns False without phone number"""
        notifier = SMSNotifier(phone_number=None, api_key=self.api_key)
        self.assertFalse(notifier.is_configured())

    def test_is_configured_false_no_api_key(self):
        """Test is_configured returns False without API key"""
        notifier = SMSNotifier(phone_number=self.phone_number, api_key=None)
        self.assertFalse(notifier.is_configured())

    @patch("requests.post")
    def test_send_notification_success(self, mock_post):
        """Test successful SMS notification sending"""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "textId": "12345"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)
        result = notifier.send_notification(url="http://example.com", message="Content changed")

        self.assertTrue(result)
        mock_post.assert_called_once()
        call_args = mock_post.call_args[1]
        self.assertEqual(call_args["data"]["phone"], self.phone_number)
        self.assertEqual(call_args["data"]["key"], self.api_key)
        self.assertIn("WEBSITE CHANGE DETECTED", call_args["data"]["message"])

    def test_send_notification_not_configured(self):
        """Test sending notification when not configured"""
        notifier = SMSNotifier(phone_number=None, api_key=None)
        result = notifier.send_notification("http://example.com", "test message")
        self.assertFalse(result)

    @patch("requests.post")
    def test_send_notification_api_error(self, mock_post):
        """Test handling TextBelt API errors"""
        mock_response = Mock()
        mock_response.json.return_value = {"success": False, "error": "Invalid API key"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)
        result = notifier.send_notification("http://example.com", "test message")

        self.assertFalse(result)

    @patch("requests.post")
    def test_send_notification_http_error(self, mock_post):
        """Test handling HTTP errors"""
        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)
        result = notifier.send_notification("http://example.com", "test message")

        self.assertFalse(result)

    @patch("requests.post")
    def test_send_notification_generic_exception(self, mock_post):
        """Test generic exception handling in send_notification"""
        mock_post.side_effect = ValueError("Some generic error")

        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)

        with patch("logging.error") as mock_log:
            result = notifier.send_notification("http://example.com", "Some changes")

            self.assertFalse(result)
            # Check that error logging was called (multiple calls happen, check the last one)
            mock_log.assert_any_call("[SMS] Error details: Some generic error")

    @patch("requests.post")
    def test_test_notification_success(self, mock_post):
        """Test successful test notification"""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "textId": "test-12345"}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)
        result = notifier.test_notification()

        self.assertTrue(result["success"])
        self.assertEqual(result["text_id"], "test-12345")
        self.assertEqual(result["details"]["phone_number"], self.phone_number)

    @patch("requests.post")
    def test_test_notification_failure(self, mock_post):
        """Test failed test notification"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid phone number",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        notifier = SMSNotifier(phone_number=self.phone_number, api_key=self.api_key)
        result = notifier.test_notification()

        self.assertFalse(result["success"])
        self.assertIn("Invalid phone number", result["error"])

    def test_test_notification_not_configured(self):
        """Test test_notification when not configured"""
        notifier = SMSNotifier()

        result = notifier.test_notification()

        self.assertEqual(
            result,
            {
                "success": False,
                "error": "SMS notifications not configured",
                "details": {
                    "phone_number": False,
                    "api_key": False,
                },
            },
        )


class TestCreateNotifierFromEnv(unittest.TestCase):
    """Test cases for environment-based notifier creation"""

    @patch.dict(
        os.environ,
        {
            "SMS_PHONE_NUMBER": "+1234567890",
            "TEXTBELT_API_KEY": "test_key",
        },
    )
    def test_create_from_env_with_all_vars(self):
        """Test creating notifier from environment variables"""
        notifier = create_notifier_from_env()

        self.assertEqual(notifier.phone_number, "+1234567890")
        self.assertEqual(notifier.api_key, "test_key")

    @patch.dict(os.environ, {}, clear=True)
    def test_create_from_env_missing_vars(self):
        """Test creating notifier with missing environment variables"""
        notifier = create_notifier_from_env(load_dotenv=False)
        self.assertIsNone(notifier.phone_number)
        self.assertIsNone(notifier.api_key)

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_create_from_env_with_dotenv(self, mock_open, mock_exists):
        """Test creating notifier from .env file"""
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.__iter__.return_value = [
            "SMS_PHONE_NUMBER=+1234567890\n",
            "TEXTBELT_API_KEY=test_key\n",
        ]

        with patch.dict(os.environ, {}, clear=True):
            notifier = create_notifier_from_env()
            self.assertEqual(notifier.phone_number, "+1234567890")
            self.assertEqual(notifier.api_key, "test_key")


class TestURLWatcherSMSIntegration(unittest.TestCase):
    """Test cases for URL watcher SMS integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_cache_file = "test_sms_cache.json"
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

    @patch("requests.get")
    def test_url_watcher_with_sms_notifier(self, mock_get):
        """Test URL watcher with SMS notifications enabled"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.text = "Initial content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock SMS notifier
        mock_notifier = Mock()
        mock_notifier.is_configured.return_value = True
        mock_notifier.send_notification.return_value = True

        # Create watcher with SMS notifier
        watcher = URLWatcher(storage_file=self.test_cache_file, sms_notifier=mock_notifier)

        # First check - should not send SMS (first time)
        changed, diff = watcher.check_url("http://example.com")
        self.assertFalse(changed)
        mock_notifier.send_notification.assert_not_called()

        # Change content and check again
        mock_response.text = "Changed content"
        changed, diff = watcher.check_url("http://example.com")

        # Should detect change and send SMS
        self.assertTrue(changed)
        mock_notifier.send_notification.assert_called_once_with("http://example.com", diff)

    @patch("requests.get")
    def test_url_watcher_without_sms_notifier(self, mock_get):
        """Test URL watcher without SMS notifications"""
        mock_response = Mock()
        mock_response.text = "Content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        watcher = URLWatcher(storage_file=self.test_cache_file)

        # Should work normally without SMS notifier
        changed, diff = watcher.check_url("http://example.com")
        self.assertFalse(changed)  # First time check

    @patch("requests.get")
    def test_url_watcher_sms_error_handling(self, mock_get):
        """Test URL watcher handles SMS notification errors gracefully"""
        mock_response = Mock()
        mock_response.text = "Initial content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock SMS notifier that raises exception
        mock_notifier = Mock()
        mock_notifier.is_configured.return_value = True
        mock_notifier.send_notification.side_effect = Exception("SMS failed")

        watcher = URLWatcher(storage_file=self.test_cache_file, sms_notifier=mock_notifier)

        # First check
        watcher.check_url("http://example.com")

        # Change content - should handle SMS error gracefully
        mock_response.text = "Changed content"
        with patch("logging.error") as mock_log:
            changed, diff = watcher.check_url("http://example.com")

            # Should still detect change despite SMS error
            self.assertTrue(changed)
            mock_log.assert_called()


if __name__ == "__main__":
    # Set up logging for tests
    logging.basicConfig(level=logging.INFO)

    # Run tests
    unittest.main()
