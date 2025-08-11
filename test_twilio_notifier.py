#!/usr/bin/env python3
"""
Test suite for Twilio SMS notification functionality
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from twilio_notifier import TwilioNotifier, create_notifier_from_env


class TestTwilioNotifier:
    """Test the TwilioNotifier class functionality"""

    def test_init_without_credentials(self):
        """Test initializing without credentials"""
        notifier = TwilioNotifier()
        assert notifier.account_sid is None
        assert notifier.auth_token is None
        assert notifier.from_phone is None
        assert notifier.to_phone is None
        assert not notifier.is_configured()

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch("twilio_notifier.Client")
    def test_init_with_credentials(self, mock_client):
        """Test initializing with credentials"""
        notifier = TwilioNotifier(
            account_sid="ACtest123",
            auth_token="token123",
            from_phone="+15551234567",
            to_phone="+19876543210",
        )

        assert notifier.account_sid == "ACtest123"
        assert notifier.auth_token == "token123"
        assert notifier.from_phone == "+15551234567"
        assert notifier.to_phone == "+19876543210"
        mock_client.assert_called_once_with("ACtest123", "token123")

    def test_is_configured_false_cases(self):
        """Test is_configured returns False for incomplete configuration"""
        # No credentials
        notifier = TwilioNotifier()
        assert not notifier.is_configured()

        # Missing phone numbers
        notifier = TwilioNotifier(account_sid="test", auth_token="test")
        assert not notifier.is_configured()

        # Missing auth token
        notifier = TwilioNotifier(
            account_sid="test", from_phone="+1234567890", to_phone="+1987654321"
        )
        assert not notifier.is_configured()

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch("twilio_notifier.Client")
    def test_is_configured_true(self, mock_client):
        """Test is_configured returns True for complete configuration"""
        mock_client.return_value = Mock()

        notifier = TwilioNotifier(
            account_sid="ACtest123",
            auth_token="token123",
            from_phone="+15551234567",
            to_phone="+19876543210",
        )

        assert notifier.is_configured()

    @patch("twilio_notifier.TWILIO_AVAILABLE", False)
    def test_is_configured_false_when_twilio_unavailable(self):
        """Test is_configured returns False when Twilio package unavailable"""
        notifier = TwilioNotifier(
            account_sid="ACtest123",
            auth_token="token123",
            from_phone="+15551234567",
            to_phone="+19876543210",
        )

        assert not notifier.is_configured()

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch("twilio_notifier.Client")
    def test_send_notification_success(self, mock_client):
        """Test successful SMS notification sending"""
        # Setup mocks
        mock_message = Mock()
        mock_message.sid = "SMtest123"
        mock_client.return_value.messages.create.return_value = mock_message

        notifier = TwilioNotifier(
            account_sid="ACtest123",
            auth_token="token123",
            from_phone="+15551234567",
            to_phone="+19876543210",
        )

        # Send notification
        result = notifier.send_notification(
            url="https://example.com", message="Test change detected"
        )

        assert result is True
        mock_client.return_value.messages.create.assert_called_once()

        # Check the call arguments
        call_args = mock_client.return_value.messages.create.call_args
        assert call_args[1]["from_"] == "+15551234567"
        assert call_args[1]["to"] == "+19876543210"
        assert "URL CHANGE DETECTED" in call_args[1]["body"]
        assert "https://example.com" in call_args[1]["body"]

    def test_send_notification_not_configured(self):
        """Test send_notification fails when not configured"""
        notifier = TwilioNotifier()

        result = notifier.send_notification(url="https://example.com", message="Test message")

        assert result is False

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch("twilio_notifier.Client")
    def test_send_notification_twilio_exception(self, mock_client):
        """Test send_notification handles Twilio exceptions"""
        # Create a mock exception that inherits from Exception
        mock_exception = Exception("Test Twilio error")
        mock_client.return_value.messages.create.side_effect = mock_exception

        notifier = TwilioNotifier(
            account_sid="ACtest123",
            auth_token="token123",
            from_phone="+15551234567",
            to_phone="+19876543210",
        )

        result = notifier.send_notification(url="https://example.com", message="Test message")

        assert result is False

    def test_format_message(self):
        """Test message formatting"""
        notifier = TwilioNotifier()

        message = notifier._format_message(
            url="https://example.com", content="Line changed from A to B"
        )

        assert "URL CHANGE DETECTED" in message
        assert "https://example.com" in message
        assert "Line changed from A to B" in message
        assert "Powered by URL Watcher + Twilio" in message

    def test_format_message_truncation(self):
        """Test message truncation for long content"""
        notifier = TwilioNotifier()

        # Create very long content
        long_content = "A" * 1500

        message = notifier._format_message(url="https://example.com", content=long_content)

        # Should be truncated and have "..." at the end
        assert len(message) < 1600  # Under SMS limit
        assert message.count("A") < 1500  # Content was truncated
        assert "..." in message

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch("twilio_notifier.Client")
    def test_test_notification_success(self, mock_client):
        """Test successful test notification"""
        mock_message = Mock()
        mock_message.sid = "SMtest123"
        mock_message.status = "sent"
        mock_client.return_value.messages.create.return_value = mock_message

        notifier = TwilioNotifier(
            account_sid="ACtest123",
            auth_token="token123",
            from_phone="+15551234567",
            to_phone="+19876543210",
        )

        result = notifier.test_notification()

        assert result["success"] is True
        assert result["message_id"] == "SMtest123"
        assert result["status"] == "sent"

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch("twilio_notifier.Client")
    def test_test_notification_not_configured(self, mock_client):
        """Test test notification when not configured"""
        notifier = TwilioNotifier()  # No credentials provided

        result = notifier.test_notification()

        assert result["success"] is False
        assert "not configured" in result["message"]
        assert "Missing:" in result["error"]

    @patch("twilio_notifier.TWILIO_AVAILABLE", False)
    def test_test_notification_twilio_unavailable(self):
        """Test test notification when Twilio package unavailable"""
        notifier = TwilioNotifier()

        result = notifier.test_notification()

        assert result["success"] is False
        assert "not installed" in result["message"]


class TestCreateNotifierFromEnv:
    """Test the create_notifier_from_env function"""

    @patch("twilio_notifier.TWILIO_AVAILABLE", True)
    @patch.dict(
        os.environ,
        {
            "TWILIO_ACCOUNT_SID": "ACtest123",
            "TWILIO_AUTH_TOKEN": "token123",
            "TWILIO_FROM_PHONE": "+15551234567",
            "TWILIO_TO_PHONE": "+19876543210",
        },
    )
    @patch("twilio_notifier.Client")
    def test_create_from_env_success(self, mock_client):
        """Test creating notifier from environment variables"""
        notifier = create_notifier_from_env()

        assert notifier.account_sid == "ACtest123"
        assert notifier.auth_token == "token123"
        assert notifier.from_phone == "+15551234567"
        assert notifier.to_phone == "+19876543210"

    @patch.dict(os.environ, {}, clear=True)
    def test_create_from_env_no_vars(self):
        """Test creating notifier with no environment variables"""
        notifier = create_notifier_from_env()

        assert notifier.account_sid is None
        assert notifier.auth_token is None
        assert notifier.from_phone is None
        assert notifier.to_phone is None
        assert not notifier.is_configured()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
