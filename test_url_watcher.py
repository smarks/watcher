#!/usr/bin/env python3
"""
Unit tests for URL Watcher
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, mock_open, MagicMock, Mock
import requests
from url_watcher import URLWatcher


class TestURLWatcher(unittest.TestCase):
    
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.watcher = URLWatcher(storage_file=self.temp_file.name)
        self.test_url = "https://example.com"
    
    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_init_with_new_cache_file(self):
        """Test initialization with non-existent cache file"""
        non_existent_file = "/tmp/non_existent_cache.json"
        if os.path.exists(non_existent_file):
            os.unlink(non_existent_file)
        
        watcher = URLWatcher(storage_file=non_existent_file)
        self.assertEqual(watcher.cache, {})
        self.assertEqual(watcher.storage_file, non_existent_file)
    
    def test_init_with_existing_cache_file(self):
        """Test initialization with existing cache file"""
        test_cache = {
            "https://test.com": {
                "content": "test content",
                "hash": "testhash",
                "last_checked": "2023-01-01T00:00:00"
            }
        }
        
        with open(self.temp_file.name, 'w') as f:
            json.dump(test_cache, f)
        
        watcher = URLWatcher(storage_file=self.temp_file.name)
        self.assertEqual(watcher.cache, test_cache)
    
    def test_init_with_corrupted_cache_file(self):
        """Test initialization with corrupted cache file"""
        with open(self.temp_file.name, 'w') as f:
            f.write("invalid json content")
        
        watcher = URLWatcher(storage_file=self.temp_file.name)
        self.assertEqual(watcher.cache, {})
    
    @patch('requests.get')
    def test_fetch_url_content_success(self, mock_get):
        """Test successful URL content fetching"""
        mock_response = MagicMock()
        mock_response.text = "Hello World"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        content = self.watcher._fetch_url_content(self.test_url)
        self.assertEqual(content, "Hello World")
        mock_get.assert_called_once_with(self.test_url, timeout=10)
    
    @patch('requests.get')
    def test_fetch_url_content_failure(self, mock_get):
        """Test URL content fetching failure"""
        mock_get.side_effect = requests.RequestException("Network error")
        
        with self.assertRaises(Exception) as context:
            self.watcher._fetch_url_content(self.test_url)
        
        self.assertIn("Failed to fetch URL", str(context.exception))
    
    def test_get_content_hash(self):
        """Test content hashing"""
        content = "Hello World"
        hash1 = self.watcher._get_content_hash(content)
        hash2 = self.watcher._get_content_hash(content)
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 produces 64-char hex string
        
        different_content = "Hello Mars"
        hash3 = self.watcher._get_content_hash(different_content)
        self.assertNotEqual(hash1, hash3)
    
    @patch('url_watcher.URLWatcher._fetch_url_content')
    def test_check_url_first_time(self, mock_fetch):
        """Test checking URL for the first time"""
        mock_fetch.return_value = "Initial content"
        
        changed, difference = self.watcher.check_url(self.test_url)
        
        self.assertFalse(changed)
        self.assertIn("First time checking", difference)
        self.assertIn(self.test_url, self.watcher.cache)
        self.assertEqual(self.watcher.cache[self.test_url]['content'], "Initial content")
    
    @patch('url_watcher.URLWatcher._fetch_url_content')
    def test_check_url_no_change(self, mock_fetch):
        """Test checking URL with no content change"""
        content = "Same content"
        mock_fetch.return_value = content
        
        # First check
        self.watcher.check_url(self.test_url)
        
        # Second check with same content
        changed, difference = self.watcher.check_url(self.test_url)
        
        self.assertFalse(changed)
        self.assertIsNone(difference)
    
    @patch('url_watcher.URLWatcher._fetch_url_content')
    def test_check_url_with_change(self, mock_fetch):
        """Test checking URL with content change"""
        # First check
        mock_fetch.return_value = "Original content"
        self.watcher.check_url(self.test_url)
        
        # Second check with different content
        mock_fetch.return_value = "Modified content"
        changed, difference = self.watcher.check_url(self.test_url)
        
        self.assertTrue(changed)
        self.assertIsNotNone(difference)
        self.assertIn("Original content", difference)
        self.assertIn("Modified content", difference)
    
    def test_generate_diff(self):
        """Test diff generation"""
        old_content = "Line 1\nLine 2\nLine 3"
        new_content = "Line 1\nModified Line 2\nLine 3"
        
        diff = self.watcher._generate_diff(old_content, new_content, self.test_url)
        
        self.assertIn("Line 2", diff)
        self.assertIn("Modified Line 2", diff)
        self.assertIn("---", diff)
        self.assertIn("+++", diff)
    
    def test_generate_diff_no_changes(self):
        """Test diff generation with identical content"""
        content = "Same content"
        
        diff = self.watcher._generate_diff(content, content, self.test_url)
        
        self.assertIn("no line-by-line differences", diff)
    
    def test_save_and_load_cache(self):
        """Test cache saving and loading"""
        test_data = {
            self.test_url: {
                "content": "test content",
                "hash": "testhash123",
                "last_checked": "2023-01-01T00:00:00"
            }
        }
        
        self.watcher.cache = test_data
        self.watcher._save_cache()
        
        # Create new watcher instance to test loading
        new_watcher = URLWatcher(storage_file=self.temp_file.name)
        self.assertEqual(new_watcher.cache, test_data)
    
    @patch('requests.get')
    def test_check_url_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = requests.RequestException("Connection timeout")
        
        with self.assertRaises(Exception) as context:
            self.watcher.check_url(self.test_url)
        
        self.assertIn("Failed to fetch URL", str(context.exception))
    
    @patch('requests.get')
    def test_check_url_http_error(self, mock_get):
        """Test handling of HTTP errors"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception) as context:
            self.watcher.check_url(self.test_url)
        
        self.assertIn("Failed to fetch URL", str(context.exception))
    
    @patch('url_watcher.URLWatcher._fetch_url_content')
    def test_cache_persistence(self, mock_fetch):
        """Test that cache persists between instances"""
        mock_fetch.return_value = "Persistent content"
        
        # First watcher instance
        watcher1 = URLWatcher(storage_file=self.temp_file.name)
        watcher1.check_url(self.test_url)
        
        # Second watcher instance should load the cache
        watcher2 = URLWatcher(storage_file=self.temp_file.name)
        self.assertIn(self.test_url, watcher2.cache)
        self.assertEqual(watcher2.cache[self.test_url]['content'], "Persistent content")
    
    def test_multiline_content_diff(self):
        """Test diff generation with multiline content"""
        old_content = """Line 1
Line 2
Line 3
Line 4"""
        
        new_content = """Line 1
Modified Line 2
Line 3
New Line 4
Line 5"""
        
        diff = self.watcher._generate_diff(old_content, new_content, self.test_url)
        
        self.assertIn("-Line 2", diff)
        self.assertIn("+Modified Line 2", diff)
        self.assertIn("-Line 4", diff)
        self.assertIn("+New Line 4", diff)
        self.assertIn("+Line 5", diff)

    @patch('time.sleep')
    @patch('builtins.print')
    @patch('requests.get')
    def test_watch_continuously_keyboard_interrupt(self, mock_get, mock_print, mock_sleep):
        """Test watch_continuously stops on KeyboardInterrupt"""
        mock_response = Mock()
        mock_response.text = "Content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Simulate KeyboardInterrupt after first iteration
        mock_sleep.side_effect = KeyboardInterrupt()
        
        self.watcher.watch_continuously(self.test_url, min_interval=1, max_interval=2)
        
        # Should handle KeyboardInterrupt gracefully
        mock_print.assert_any_call("\n\nStopping continuous monitoring.")

    @patch('time.sleep')
    @patch('builtins.print')
    @patch('requests.get')
    def test_watch_continuously_with_changes(self, mock_get, mock_print, mock_sleep):
        """Test watch_continuously detects changes"""
        # Setup responses - first call returns initial content, second returns changed content
        initial_response = Mock()
        initial_response.text = "Initial content"
        initial_response.raise_for_status.return_value = None
        
        changed_response = Mock()
        changed_response.text = "Changed content"
        changed_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [initial_response, changed_response]
        
        # Simulate KeyboardInterrupt after second iteration
        def sleep_side_effect(seconds):
            if mock_get.call_count >= 2:
                raise KeyboardInterrupt()
        mock_sleep.side_effect = sleep_side_effect
        
        self.watcher.watch_continuously(self.test_url, min_interval=1, max_interval=1)
        
        # Should detect changes
        mock_print.assert_any_call("✅ Content has CHANGED!")

    @patch('time.sleep')
    @patch('builtins.print')
    @patch('requests.get')
    def test_watch_continuously_handles_exceptions(self, mock_get, mock_print, mock_sleep):
        """Test watch_continuously handles request exceptions"""
        # First call succeeds, second raises exception
        initial_response = Mock()
        initial_response.text = "Content"
        initial_response.raise_for_status.return_value = None
        
        mock_get.side_effect = [initial_response, Exception("Network error")]
        
        # Simulate KeyboardInterrupt after handling exception
        def sleep_side_effect(seconds):
            if mock_get.call_count >= 2:
                raise KeyboardInterrupt()
        mock_sleep.side_effect = sleep_side_effect
        
        self.watcher.watch_continuously(self.test_url, min_interval=1, max_interval=1)
        
        # Should handle exception gracefully
        mock_print.assert_any_call("Error during check: Network error")


class TestMainCLI(unittest.TestCase):
    """Test cases for main CLI function"""
    
    def setUp(self):
        self.test_cache_file = "test_cache_cli.json"
    
    def tearDown(self):
        if os.path.exists(self.test_cache_file):
            os.remove(self.test_cache_file)

    @patch('sys.argv', ['url_watcher.py'])
    @patch('builtins.print')
    def test_main_no_arguments(self, mock_print):
        """Test main with no arguments shows usage"""
        from url_watcher import main
        
        with self.assertRaises(SystemExit) as cm:
            main()
        
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("Usage: python url_watcher.py <URL> [--continuous] [--sms]")

    @patch('sys.argv', ['url_watcher.py', 'url', 'extra', 'args', 'too', 'many'])
    @patch('builtins.print')  
    def test_main_too_many_arguments(self, mock_print):
        """Test main with too many arguments shows usage"""
        from url_watcher import main
        
        with self.assertRaises(SystemExit) as cm:
            main()
        
        self.assertEqual(cm.exception.code, 1)
        mock_print.assert_any_call("Usage: python url_watcher.py <URL> [--continuous] [--sms]")

    @patch('sys.argv', ['url_watcher.py', 'http://example.com'])
    @patch('requests.get')
    @patch('builtins.print')
    def test_main_single_check_no_change(self, mock_print, mock_get):
        """Test main single check with no changes"""
        mock_response = Mock()
        mock_response.text = "Content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        from url_watcher import main
        
        main()
        
        mock_print.assert_any_call("❌ No changes detected")

    @patch('sys.argv', ['url_watcher.py', 'http://example.com'])
    @patch('requests.get')
    @patch('builtins.print')
    def test_main_single_check_with_change(self, mock_print, mock_get):
        """Test main single check with changes"""
        # Simulate cache already exists with different content
        cache_data = {
            'http://example.com': {
                'content_hash': 'old_hash',
                'last_modified': '2023-01-01 00:00:00'
            }
        }
        with open(self.test_cache_file, 'w') as f:
            json.dump(cache_data, f)
        
        mock_response = Mock()
        mock_response.text = "New content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        from url_watcher import main
        
        # Patch URLWatcher to use our test cache file
        with patch('url_watcher.URLWatcher') as mock_watcher_class:
            mock_watcher = Mock()
            mock_watcher.check_url.return_value = (True, "Some diff")
            mock_watcher_class.return_value = mock_watcher
            
            main()
            
            mock_print.assert_any_call("✅ Content has CHANGED!")

    @patch('sys.argv', ['url_watcher.py', 'http://example.com', '--continuous'])
    @patch('builtins.print')
    def test_main_continuous_mode(self, mock_print):
        """Test main in continuous mode"""
        from url_watcher import main
        
        with patch('url_watcher.URLWatcher') as mock_watcher_class:
            mock_watcher = Mock()
            mock_watcher_class.return_value = mock_watcher
            
            main()
            
            mock_watcher.watch_continuously.assert_called_once_with('http://example.com')

    @patch('sys.argv', ['url_watcher.py', 'http://example.com', '--sms'])
    @patch('builtins.print')
    def test_main_with_sms_not_configured(self, mock_print):
        """Test main with SMS but not configured"""
        from url_watcher import main
        
        with patch('url_watcher.create_notifier_from_env') as mock_create_notifier:
            mock_notifier = Mock()
            mock_notifier.is_configured.return_value = False
            mock_create_notifier.return_value = mock_notifier
            
            with patch('url_watcher.URLWatcher') as mock_watcher_class:
                mock_watcher = Mock()
                mock_watcher.check_url.return_value = (False, "")
                mock_watcher_class.return_value = mock_watcher
                
                main()
                
                mock_print.assert_any_call("⚠️  SMS notifications requested but not properly configured")

    @patch('sys.argv', ['url_watcher.py', 'http://example.com', '--sms'])
    @patch('builtins.print')
    def test_main_with_sms_configured(self, mock_print):
        """Test main with SMS properly configured"""
        from url_watcher import main
        
        with patch('url_watcher.create_notifier_from_env') as mock_create_notifier:
            mock_notifier = Mock()
            mock_notifier.is_configured.return_value = True
            mock_create_notifier.return_value = mock_notifier
            
            with patch('url_watcher.URLWatcher') as mock_watcher_class:
                mock_watcher = Mock()
                mock_watcher.check_url.return_value = (False, "")
                mock_watcher_class.return_value = mock_watcher
                
                main()
                
                mock_print.assert_any_call("📱 SMS notifications enabled")

    @patch('sys.argv', ['url_watcher.py', 'http://example.com'])
    @patch('builtins.print')
    def test_main_handles_exceptions(self, mock_print):
        """Test main handles exceptions and exits with error"""
        from url_watcher import main
        
        with patch('url_watcher.URLWatcher') as mock_watcher_class:
            mock_watcher = Mock()
            mock_watcher.check_url.side_effect = Exception("Test error")
            mock_watcher_class.return_value = mock_watcher
            
            with self.assertRaises(SystemExit) as cm:
                main()
            
            self.assertEqual(cm.exception.code, 1)
            mock_print.assert_any_call("Error: Test error")


if __name__ == '__main__':
    unittest.main(verbosity=2)