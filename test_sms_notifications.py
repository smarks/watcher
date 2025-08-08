#!/usr/bin/env python3
"""
Test suite for SMS notification functionality
"""

import unittest
import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from botocore.exceptions import ClientError

from sms_notifier import SMSNotifier, create_notifier_from_env
from url_watcher import URLWatcher


class TestSMSNotifier(unittest.TestCase):
    """Test cases for SMSNotifier class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.topic_arn = "arn:aws:sns:us-east-1:123456789012:test-topic"
        self.access_key = "***REMOVED***"
        self.secret_key = "***REMOVED***"
        
    @patch('boto3.client')
    def test_initialization_with_credentials(self, mock_boto_client):
        """Test SMSNotifier initialization with credentials"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(
            topic_arn=self.topic_arn,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key
        )
        
        self.assertEqual(notifier.topic_arn, self.topic_arn)
        self.assertEqual(notifier.sns_client, mock_client)
        mock_boto_client.assert_called_once_with(
            'sns',
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name='us-east-1'
        )
    
    @patch('boto3.client')
    def test_initialization_without_credentials(self, mock_boto_client):
        """Test SMSNotifier initialization without explicit credentials"""
        mock_client = Mock()
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        
        self.assertEqual(notifier.topic_arn, self.topic_arn)
        mock_boto_client.assert_called_once_with('sns', region_name='us-east-1')
    
    def test_initialization_failure(self):
        """Test SMSNotifier initialization with invalid credentials"""
        with patch('boto3.client', side_effect=Exception("Invalid credentials")):
            notifier = SMSNotifier(
                topic_arn=self.topic_arn,
                aws_access_key_id="invalid",
                aws_secret_access_key="invalid"
            )
            self.assertIsNone(notifier.sns_client)
            self.assertFalse(notifier.is_configured())
    
    @patch('boto3.client')
    def test_is_configured_true(self, mock_boto_client):
        """Test is_configured returns True when properly set up"""
        mock_boto_client.return_value = Mock()
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        self.assertTrue(notifier.is_configured())
    
    def test_is_configured_false_no_client(self):
        """Test is_configured returns False without SNS client"""
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        notifier.sns_client = None
        self.assertFalse(notifier.is_configured())
    
    def test_is_configured_false_no_topic(self):
        """Test is_configured returns False without topic ARN"""
        with patch('boto3.client'):
            notifier = SMSNotifier(topic_arn=None)
            self.assertFalse(notifier.is_configured())
    
    @patch('boto3.client')
    def test_send_notification_success(self, mock_boto_client):
        """Test successful SMS notification sending"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'msg-123'}
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        result = notifier.send_notification(
            url="http://example.com",
            message="Content changed",
            subject="Test notification"
        )
        
        self.assertTrue(result)
        mock_client.publish.assert_called_once()
        call_args = mock_client.publish.call_args[1]
        self.assertEqual(call_args['TopicArn'], self.topic_arn)
        self.assertIn("URL CHANGE DETECTED", call_args['Message'])
        self.assertIn("http://example.com", call_args['Message'])
        self.assertIn("Content changed", call_args['Message'])
    
    @patch('boto3.client')
    def test_send_notification_not_configured(self, mock_boto_client):
        """Test sending notification when not configured"""
        notifier = SMSNotifier(topic_arn=None)
        result = notifier.send_notification("http://example.com", "test message")
        self.assertFalse(result)
    
    @patch('boto3.client')
    def test_send_notification_aws_error(self, mock_boto_client):
        """Test handling AWS SNS errors"""
        mock_client = Mock()
        mock_client.publish.side_effect = ClientError(
            {'Error': {'Code': 'InvalidParameter', 'Message': 'Invalid topic'}},
            'Publish'
        )
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        result = notifier.send_notification("http://example.com", "test message")
        
        self.assertFalse(result)
    
    @patch('boto3.client')
    def test_send_notification_message_truncation(self, mock_boto_client):
        """Test message truncation for long content"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'msg-123'}
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        long_message = "A" * 200  # Long message that should be truncated
        
        result = notifier.send_notification("http://example.com", long_message)
        
        self.assertTrue(result)
        call_args = mock_client.publish.call_args[1]
        # Check that message was truncated
        self.assertIn("A" * 100 + "...", call_args['Message'])
    
    @patch('boto3.client')
    def test_test_notification_success(self, mock_boto_client):
        """Test successful test notification"""
        mock_client = Mock()
        mock_client.publish.return_value = {'MessageId': 'test-msg-123'}
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        result = notifier.test_notification()
        
        self.assertTrue(result['success'])
        self.assertEqual(result['message_id'], 'test-msg-123')
        self.assertEqual(result['details']['topic_arn'], self.topic_arn)
    
    @patch('boto3.client')
    def test_test_notification_failure(self, mock_boto_client):
        """Test failed test notification"""
        mock_client = Mock()
        mock_client.publish.side_effect = ClientError(
            {'Error': {'Code': 'NotFound', 'Message': 'Topic not found'}},
            'Publish'
        )
        mock_boto_client.return_value = mock_client
        
        notifier = SMSNotifier(topic_arn=self.topic_arn)
        result = notifier.test_notification()
        
        self.assertFalse(result['success'])
        self.assertEqual(result['error_code'], 'NotFound')
        self.assertIn('Topic not found', result['error'])


class TestCreateNotifierFromEnv(unittest.TestCase):
    """Test cases for environment-based notifier creation"""
    
    @patch.dict(os.environ, {
        'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test-topic',
        'AWS_ACCESS_KEY_ID': '***REMOVED***',
        'AWS_SECRET_ACCESS_KEY': '***REMOVED***',
        'AWS_REGION': 'us-west-2'
    })
    @patch('boto3.client')
    def test_create_from_env_with_all_vars(self, mock_boto_client):
        """Test creating notifier from environment variables"""
        mock_boto_client.return_value = Mock()
        
        notifier = create_notifier_from_env()
        
        self.assertEqual(notifier.topic_arn, 'arn:aws:sns:us-east-1:123456789012:test-topic')
        self.assertEqual(notifier.region_name, 'us-west-2')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_create_from_env_missing_vars(self):
        """Test creating notifier with missing environment variables"""
        notifier = create_notifier_from_env()
        self.assertIsNone(notifier.topic_arn)


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
    
    @patch('requests.get')
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
        watcher = URLWatcher(
            storage_file=self.test_cache_file,
            sms_notifier=mock_notifier
        )
        
        # First check - should not send SMS (first time)
        changed, diff = watcher.check_url("http://example.com")
        self.assertFalse(changed)
        mock_notifier.send_notification.assert_not_called()
        
        # Change content and check again
        mock_response.text = "Changed content"
        changed, diff = watcher.check_url("http://example.com")
        
        # Should detect change and send SMS
        self.assertTrue(changed)
        mock_notifier.send_notification.assert_called_once_with(
            "http://example.com", diff
        )
    
    @patch('requests.get')
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
    
    @patch('requests.get')
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
        
        watcher = URLWatcher(
            storage_file=self.test_cache_file,
            sms_notifier=mock_notifier
        )
        
        # First check
        watcher.check_url("http://example.com")
        
        # Change content - should handle SMS error gracefully
        mock_response.text = "Changed content"
        with patch('logging.error') as mock_log:
            changed, diff = watcher.check_url("http://example.com")
            
            # Should still detect change despite SMS error
            self.assertTrue(changed)
            mock_log.assert_called()

    @patch('boto3.client')
    def test_send_notification_generic_exception(self, mock_boto_client):
        """Test generic exception handling in send_notification"""
        # Setup mock to raise generic exception (not ClientError)
        mock_sns_client = Mock()
        mock_sns_client.publish.side_effect = ValueError("Some generic error")
        mock_boto_client.return_value = mock_sns_client
        
        notifier = SMSNotifier("fake-topic-arn")
        
        with patch('logging.error') as mock_log:
            result = notifier.send_notification("http://example.com", "Some changes")
            
            self.assertFalse(result)
            mock_log.assert_called_with("Unexpected error sending SMS: Some generic error")

    def test_test_notification_not_configured(self):
        """Test test_notification when not configured"""
        notifier = SMSNotifier()  # No topic_arn, not configured
        
        result = notifier.test_notification()
        
        self.assertEqual(result, {
            'success': False,
            'error': 'SMS notifications not configured',
            'details': {
                'sns_client': True,  # SNS client gets created by default
                'topic_arn': False
            }
        })

    @patch('boto3.client')
    def test_test_notification_generic_exception(self, mock_boto_client):
        """Test generic exception handling in test_notification"""
        # Setup mock to raise generic exception (not ClientError)
        mock_sns_client = Mock()
        mock_sns_client.publish.side_effect = RuntimeError("Some generic error")
        mock_boto_client.return_value = mock_sns_client
        
        notifier = SMSNotifier("fake-topic-arn")
        
        result = notifier.test_notification()
        
        self.assertEqual(result, {
            'success': False,
            'error': 'Unexpected error: Some generic error'
        })


if __name__ == '__main__':
    # Set up logging for tests
    logging.basicConfig(level=logging.INFO)
    
    # Run tests
    unittest.main()