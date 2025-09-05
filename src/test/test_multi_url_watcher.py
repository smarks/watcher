#!/usr/bin/env python3
"""
Test Suite for Multi-URL Watcher with Resilience
"""

import json
import os
import tempfile

# import time  # noqa: F401
import unittest
from datetime import datetime  # timedelta unused
from unittest.mock import Mock, patch  # MagicMock unused

import requests

from multi_url_watcher import ResilientURLWatcher, load_urls_from_file


class TestResilientURLWatcher(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "test_cache.json")
        self.mock_sms = Mock()
        self.watcher = ResilientURLWatcher(
            storage_file=self.cache_file, sms_notifier=self.mock_sms, max_retries=2, retry_delay=1
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    @patch("multi_url_watcher.requests.Session.get")
    def test_successful_url_fetch(self, mock_get):
        """Test successful URL content fetching"""
        mock_response = Mock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        success, content, error = self.watcher._fetch_url_content_with_retry("http://example.com")

        self.assertTrue(success)
        self.assertEqual(content, "Test content")
        self.assertIsNone(error)

    @patch("multi_url_watcher.requests.Session.get")
    def test_url_fetch_with_retry(self, mock_get):
        """Test URL fetching with retry on failure"""
        # First attempt fails, second succeeds
        mock_response_fail = Mock()
        mock_response_fail.raise_for_status.side_effect = requests.exceptions.ConnectionError(
            "Connection failed"
        )

        mock_response_success = Mock()
        mock_response_success.text = "Success content"
        mock_response_success.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response_fail, mock_response_success]

        success, content, error = self.watcher._fetch_url_content_with_retry("http://example.com")

        self.assertTrue(success)
        self.assertEqual(content, "Success content")
        self.assertIsNone(error)
        self.assertEqual(mock_get.call_count, 2)

    @patch("multi_url_watcher.requests.Session.get")
    def test_url_fetch_permanent_failure(self, mock_get):
        """Test URL fetching with permanent failure"""
        mock_get.side_effect = requests.exceptions.ConnectionError("Permanent failure")

        success, content, error = self.watcher._fetch_url_content_with_retry("http://example.com")

        self.assertFalse(success)
        self.assertIsNone(content)
        self.assertIn("Connection failed", error)
        self.assertEqual(mock_get.call_count, 2)  # max_retries = 2

    @patch("multi_url_watcher.requests.Session.get")
    def test_first_time_check(self, mock_get):
        """Test checking URL for the first time"""
        mock_response = Mock()
        mock_response.text = "Initial content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        changed, diff, reachable = self.watcher.check_url("http://example.com")

        self.assertFalse(changed)  # No previous content to compare
        self.assertIn("First time checking", diff)
        self.assertTrue(reachable)

    @patch("multi_url_watcher.requests.Session.get")
    def test_content_change_detection(self, mock_get):
        """Test detection of content changes"""
        url = "http://example.com"

        # First check - initial content
        mock_response1 = Mock()
        mock_response1.text = "Original content"
        mock_response1.raise_for_status.return_value = None
        mock_get.return_value = mock_response1

        changed, diff, reachable = self.watcher.check_url(url)
        self.assertFalse(changed)  # First time

        # Second check - changed content
        mock_response2 = Mock()
        mock_response2.text = "Changed content"
        mock_response2.raise_for_status.return_value = None
        mock_get.return_value = mock_response2

        changed, diff, reachable = self.watcher.check_url(url)
        self.assertTrue(changed)
        self.assertIn("Original content", diff)
        self.assertIn("Changed content", diff)
        self.assertTrue(reachable)

    @patch("multi_url_watcher.requests.Session.get")
    def test_no_change_detection(self, mock_get):
        """Test when content doesn't change"""
        url = "http://example.com"
        content = "Same content"

        mock_response = Mock()
        mock_response.text = content
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # First check
        changed, diff, reachable = self.watcher.check_url(url)
        self.assertFalse(changed)

        # Second check with same content
        changed, diff, reachable = self.watcher.check_url(url)
        self.assertFalse(changed)
        self.assertIsNone(diff)
        self.assertTrue(reachable)

    @patch("multi_url_watcher.requests.Session.get")
    def test_sms_notification_on_change(self, mock_get):
        """Test SMS notification is sent when content changes"""
        url = "http://example.com"
        self.mock_sms.is_configured.return_value = True
        self.mock_sms.send_notification.return_value = True

        # Setup responses for two different contents
        mock_response1 = Mock()
        mock_response1.text = "Original content"
        mock_response1.raise_for_status.return_value = None

        mock_response2 = Mock()
        mock_response2.text = "Changed content"
        mock_response2.raise_for_status.return_value = None

        mock_get.side_effect = [mock_response1, mock_response2]

        # First check
        self.watcher.check_url(url)

        # Second check - should trigger SMS
        changed, diff, reachable = self.watcher.check_url(url)

        self.assertTrue(changed)
        self.mock_sms.send_notification.assert_called_once()
        args, _ = self.mock_sms.send_notification.call_args
        self.assertEqual(args[0], url)  # URL
        self.assertIn("Original content", args[1])  # Diff

    @patch("multi_url_watcher.requests.Session.get")
    def test_unreachable_url_handling(self, mock_get):
        """Test handling of unreachable URLs"""
        url = "http://unreachable.com"
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        changed, diff, reachable = self.watcher.check_url(url)

        self.assertFalse(changed)
        self.assertFalse(reachable)
        self.assertIn("Connection failed", diff)
        self.assertIn(url, self.watcher.unreachable_urls)

    @patch("multi_url_watcher.requests.Session.get")
    def test_recovery_from_unreachable(self, mock_get):
        """Test recovery notification when URL comes back online"""
        url = "http://recovering.com"
        self.mock_sms.is_configured.return_value = True

        # First attempt fails
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")
        changed, diff, reachable = self.watcher.check_url(url)
        self.assertFalse(reachable)

        # Second attempt succeeds
        mock_response = Mock()
        mock_response.text = "Back online!"
        mock_response.raise_for_status.return_value = None
        mock_get.side_effect = [mock_response]  # Reset side_effect
        mock_get.return_value = mock_response

        with patch.object(self.watcher, "_send_recovery_notification") as mock_recovery:
            changed, diff, reachable = self.watcher.check_url(url)
            self.assertTrue(reachable)
            mock_recovery.assert_called_once_with(url)
            self.assertNotIn(url, self.watcher.unreachable_urls)

    def test_cache_persistence(self):
        """Test that cache is saved and loaded properly"""
        url = "http://example.com"
        test_data = {
            url: {
                "content": "Test content",
                "hash": "test_hash",
                "last_checked": datetime.now().isoformat(),
                "check_count": 5,
            }
        }

        # Save test data
        self.watcher.cache = test_data
        self.watcher._save_cache()

        # Create new watcher and verify data is loaded
        new_watcher = ResilientURLWatcher(storage_file=self.cache_file)
        self.assertEqual(new_watcher.cache[url]["content"], "Test content")
        self.assertEqual(new_watcher.cache[url]["check_count"], 5)

    def test_content_hash_generation(self):
        """Test content hash generation"""
        content1 = "Same content"
        content2 = "Same content"
        content3 = "Different content"

        hash1 = self.watcher._get_content_hash(content1)
        hash2 = self.watcher._get_content_hash(content2)
        hash3 = self.watcher._get_content_hash(content3)

        self.assertEqual(hash1, hash2)
        self.assertNotEqual(hash1, hash3)

    def test_diff_generation(self):
        """Test diff generation between content versions"""
        old_content = "Line 1\\nOld Line 2\\nLine 3"
        new_content = "Line 1\\nNew Line 2\\nLine 3"
        url = "http://example.com"

        diff = self.watcher._generate_diff(old_content, new_content, url)

        self.assertIn("Old Line 2", diff)
        self.assertIn("New Line 2", diff)
        self.assertIn(url, diff)

    @patch("time.sleep")  # Mock sleep to speed up tests
    @patch("multi_url_watcher.requests.Session.get")
    def test_check_and_report_success(self, mock_get, mock_sleep):
        """Test _check_and_report method with successful check"""
        mock_response = Mock()
        mock_response.text = "Test content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        with patch("builtins.print") as mock_print:
            self.watcher._check_and_report("http://example.com")

        # Verify print was called with expected messages
        print_calls = [str(call) for call in mock_print.call_args_list]
        self.assertTrue(any("Checking: http://example.com" in call for call in print_calls))

    def test_load_urls_from_existing_file(self):
        """Test loading URLs from existing JSON file"""
        config_file = os.path.join(self.temp_dir, "test_urls.json")
        test_config = [
            {"url": "http://example.com", "interval": 60},
            {"url": "http://example.org", "interval": 300},
        ]

        with open(config_file, "w") as f:
            json.dump(test_config, f)

        loaded_config = load_urls_from_file(config_file)
        self.assertEqual(loaded_config, test_config)

    def test_load_urls_from_nonexistent_file(self):
        """Test loading URLs from non-existent file creates sample"""
        config_file = os.path.join(self.temp_dir, "nonexistent.json")

        with self.assertRaises(SystemExit):
            load_urls_from_file(config_file)

        # Verify sample file was created
        self.assertTrue(os.path.exists(config_file))
        with open(config_file, "r") as f:
            sample_config = json.load(f)
        self.assertTrue(len(sample_config) > 0)
        self.assertIn("url", sample_config[0])
        self.assertIn("interval", sample_config[0])


class TestMultiURLWatcherIntegration(unittest.TestCase):
    """Integration tests for the multi-URL watcher functionality"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, "integration_cache.json")
        self.config_file = os.path.join(self.temp_dir, "test_config.json")

        # Create test configuration
        self.test_config = [
            {"url": "http://example.com", "interval": 5},
            {"url": "http://example.org", "interval": 10},
        ]
        with open(self.config_file, "w") as f:
            json.dump(self.test_config, f)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_config_file_loading(self):
        """Test that configuration file is loaded correctly"""
        config = load_urls_from_file(self.config_file)
        self.assertEqual(len(config), 2)
        self.assertEqual(config[0]["url"], "http://example.com")
        self.assertEqual(config[0]["interval"], 5)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
