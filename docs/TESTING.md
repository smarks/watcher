# Testing Guide

## Overview

The URL Watcher project includes comprehensive test suites to ensure reliability and correctness. This guide covers all aspects of testing, from running existing tests to writing new ones.

## Table of Contents

- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [Testing Best Practices](#testing-best-practices)
- [Continuous Integration](#continuous-integration)

## Test Structure

### Test Files

```
watcher/
├── test_sms_notifications.py    # SMS functionality tests
├── test_watcher.py              # Basic URL watcher tests
└── test_url_watcher.py          # Additional watcher tests
```

### Test Categories

1. **Unit Tests**: Test individual functions and methods
2. **Integration Tests**: Test component interactions
3. **Mock Tests**: Test with simulated external services
4. **End-to-End Tests**: Test complete workflows

## Running Tests

### All Tests

```bash
# Run all SMS notification tests
python test_sms_notifications.py

# Run basic watcher tests
python test_watcher.py

# Run additional watcher tests (if exists)
python test_url_watcher.py
```

### Specific Test Classes

```bash
# Run specific test class
python -m unittest test_sms_notifications.TestSMSNotifier

# Run specific test method
python -m unittest test_sms_notifications.TestSMSNotifier.test_send_notification_success

# Verbose output
python -m unittest -v test_sms_notifications.TestSMSNotifier
```

### Test Discovery

```bash
# Discover and run all tests
python -m unittest discover -s . -p "test_*.py"

# With verbose output
python -m unittest discover -s . -p "test_*.py" -v
```

## Test Coverage

### Current Test Coverage

#### SMS Notification Tests (17 test cases)

**TestSMSNotifier Class:**
- ✅ `test_initialization_with_credentials` - Test SMSNotifier setup with explicit credentials
- ✅ `test_initialization_without_credentials` - Test SMSNotifier setup with environment/IAM credentials
- ✅ `test_initialization_failure` - Test handling of invalid credentials
- ✅ `test_is_configured_true` - Test configuration validation (positive case)
- ✅ `test_is_configured_false_no_client` - Test configuration validation without SNS client
- ✅ `test_is_configured_false_no_topic` - Test configuration validation without topic ARN
- ✅ `test_send_notification_success` - Test successful SMS sending
- ✅ `test_send_notification_not_configured` - Test SMS sending when not configured
- ✅ `test_send_notification_aws_error` - Test handling of AWS SNS errors
- ✅ `test_send_notification_message_truncation` - Test message truncation for SMS limits
- ✅ `test_test_notification_success` - Test successful test notification
- ✅ `test_test_notification_failure` - Test failed test notification

**TestCreateNotifierFromEnv Class:**
- ✅ `test_create_from_env_with_all_vars` - Test environment variable configuration
- ✅ `test_create_from_env_missing_vars` - Test missing environment variables

**TestURLWatcherSMSIntegration Class:**
- ✅ `test_url_watcher_with_sms_notifier` - Test URL watcher with SMS enabled
- ✅ `test_url_watcher_without_sms_notifier` - Test URL watcher without SMS
- ✅ `test_url_watcher_sms_error_handling` - Test graceful SMS error handling

#### URL Watcher Tests

**Basic Functionality:**
- URL content fetching and caching
- Change detection with diff generation
- Continuous monitoring with intervals
- Error handling for network issues

### Measuring Coverage

Install coverage tools:
```bash
pip install coverage
```

Run tests with coverage:
```bash
# Run with coverage measurement
coverage run -m unittest test_sms_notifications.py

# Generate coverage report
coverage report

# Generate HTML coverage report
coverage html
```

**Example Coverage Report:**
```
Name                      Stmts   Miss  Cover
---------------------------------------------
sms_notifier.py              89      5    94%
url_watcher.py              112     12    89%
test_sms_notifications.py   298      0   100%
---------------------------------------------
TOTAL                       499     17    97%
```

## Writing New Tests

### Test File Structure

```python
#!/usr/bin/env python3
"""
Test suite for [component name]
"""

import unittest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from your_module import YourClass

class TestYourClass(unittest.TestCase):
    """Test cases for YourClass"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_data = "example"
        self.mock_object = Mock()

    def tearDown(self):
        """Clean up after each test method"""
        # Remove test files, reset state, etc.
        pass

    def test_basic_functionality(self):
        """Test basic functionality - descriptive docstring"""
        # Arrange
        expected_result = "expected"

        # Act
        actual_result = your_function("input")

        # Assert
        self.assertEqual(actual_result, expected_result)

    def test_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            your_function("invalid_input")

if __name__ == '__main__':
    unittest.main()
```

### Mock External Dependencies

#### Mocking HTTP Requests

```python
@patch('requests.get')
def test_url_fetch(self, mock_get):
    """Test URL fetching with mocked requests"""
    # Setup mock response
    mock_response = Mock()
    mock_response.text = "<html>Test content</html>"
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    # Test the function
    watcher = URLWatcher()
    content = watcher._fetch_url_content("http://example.com")

    # Verify
    self.assertEqual(content, "<html>Test content</html>")
    mock_get.assert_called_once_with("http://example.com", timeout=10)
```

#### Mocking AWS Services

```python
@patch('boto3.client')
def test_sns_functionality(self, mock_boto_client):
    """Test SNS functionality with mocked AWS"""
    # Setup mock SNS client
    mock_client = Mock()
    mock_client.publish.return_value = {'MessageId': 'test-123'}
    mock_boto_client.return_value = mock_client

    # Test SMS notification
    notifier = SMSNotifier(topic_arn="arn:aws:sns:us-east-1:123456789012:test")
    result = notifier.send_notification("http://example.com", "test message")

    # Verify
    self.assertTrue(result)
    mock_client.publish.assert_called_once()
```

#### Mocking File System Operations

```python
@patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"test": "data"}')
@patch('os.path.exists')
def test_cache_loading(self, mock_exists, mock_file):
    """Test cache loading with mocked file operations"""
    mock_exists.return_value = True

    watcher = URLWatcher()
    cache = watcher._load_cache()

    self.assertEqual(cache, {"test": "data"})
    mock_file.assert_called_once_with(watcher.storage_file, 'r')
```

### Test Data Management

#### Temporary Files

```python
import tempfile
import os

class TestWithTempFiles(unittest.TestCase):
    def setUp(self):
        """Create temporary files for testing"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_cache = os.path.join(self.temp_dir, "test_cache.json")

    def tearDown(self):
        """Clean up temporary files"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_with_temp_file(self):
        """Test functionality with temporary file"""
        watcher = URLWatcher(storage_file=self.temp_cache)
        # Test operations...
```

#### Test Fixtures

```python
class TestWithFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures for entire test class"""
        cls.sample_html = """
        <!DOCTYPE html>
        <html>
        <body>
            <h1>Test Page</h1>
            <p>Test content</p>
        </body>
        </html>
        """

        cls.sample_json = {
            "id": 123,
            "name": "Test Item",
            "timestamp": "2025-07-29T16:45:32Z"
        }

    def test_html_parsing(self):
        """Test HTML parsing with fixture data"""
        # Use self.sample_html in test
        pass
```

### Integration Testing

#### Local Server Testing

```python
import threading
import http.server
import socketserver
from time import sleep

class TestWithLocalServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start local HTTP server for testing"""
        cls.port = 8888
        cls.server_thread = None
        cls._start_server()

    @classmethod
    def _start_server(cls):
        """Start HTTP server in background thread"""
        def run_server():
            handler = http.server.SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", cls.port), handler) as httpd:
                cls.httpd = httpd
                httpd.serve_forever()

        cls.server_thread = threading.Thread(target=run_server, daemon=True)
        cls.server_thread.start()
        sleep(0.5)  # Give server time to start

    @classmethod
    def tearDownClass(cls):
        """Stop local HTTP server"""
        if hasattr(cls, 'httpd'):
            cls.httpd.shutdown()

    def test_local_server_monitoring(self):
        """Test monitoring of local HTTP server"""
        watcher = URLWatcher()
        changed, diff = watcher.check_url(f"http://localhost:{self.port}")

        # First check should be "no change" (first time)
        self.assertFalse(changed)
```

#### Database Testing

```python
import sqlite3
import tempfile

class TestWithDatabase(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.db_file.name
        self.db_file.close()

        # Initialize test database
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE test_data (
                id INTEGER PRIMARY KEY,
                content TEXT
            )
        """)
        self.conn.commit()

    def tearDown(self):
        """Clean up test database"""
        self.conn.close()
        os.unlink(self.db_path)

    def test_database_operations(self):
        """Test database operations"""
        # Test database functionality
        pass
```

### Performance Testing

```python
import time
from functools import wraps

def time_test(func):
    """Decorator to measure test execution time"""
    @wraps(func)
    def wrapper(self):
        start_time = time.time()
        result = func(self)
        end_time = time.time()

        execution_time = end_time - start_time
        print(f"{func.__name__} took {execution_time:.4f} seconds")

        # Assert performance requirements
        self.assertLess(execution_time, 1.0, "Test took too long")

        return result
    return wrapper

class TestPerformance(unittest.TestCase):
    @time_test
    def test_url_checking_performance(self):
        """Test URL checking performance"""
        watcher = URLWatcher()

        # Test with mocked fast response
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.text = "test content"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # This should complete quickly
            changed, diff = watcher.check_url("http://example.com")
```

## Testing Best Practices

### Test Organization

1. **Group Related Tests**: Use test classes to group related functionality
2. **Descriptive Names**: Use clear, descriptive test method names
3. **Single Responsibility**: Each test should test one specific behavior
4. **Arrange-Act-Assert**: Structure tests with clear setup, execution, and verification

### Mock Usage

```python
# Good: Mock external dependencies
@patch('requests.get')
def test_network_request(self, mock_get):
    # Test implementation
    pass

# Good: Mock time-dependent functions
@patch('datetime.datetime')
def test_timestamp_generation(self, mock_datetime):
    mock_datetime.now.return_value = datetime(2025, 7, 29, 16, 45, 32)
    # Test implementation
    pass

# Avoid: Over-mocking internal logic
# Don't mock everything - test real functionality where possible
```

### Error Testing

```python
def test_error_conditions(self):
    """Test various error conditions"""
    watcher = URLWatcher()

    # Test network errors
    with patch('requests.get', side_effect=requests.ConnectionError()):
        with self.assertRaises(Exception):
            watcher.check_url("http://example.com")

    # Test timeout errors
    with patch('requests.get', side_effect=requests.Timeout()):
        with self.assertRaises(Exception):
            watcher.check_url("http://example.com")

    # Test HTTP errors
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
    with patch('requests.get', return_value=mock_response):
        with self.assertRaises(Exception):
            watcher.check_url("http://example.com")
```

### Environment Testing

```python
@patch.dict(os.environ, {
    'AWS_ACCESS_KEY_ID': 'test_key',
    'AWS_SECRET_ACCESS_KEY': 'test_secret',
    'SNS_TOPIC_ARN': 'arn:aws:sns:us-east-1:123456789012:test'
})
def test_environment_configuration(self):
    """Test configuration from environment variables"""
    notifier = create_notifier_from_env()
    self.assertIsNotNone(notifier.topic_arn)
    self.assertEqual(notifier.topic_arn, 'arn:aws:sns:us-east-1:123456789012:test')
```

## Test Utilities

### Custom Assertions

```python
class URLWatcherTestCase(unittest.TestCase):
    """Base test case with custom assertions for URL Watcher"""

    def assertURLChanged(self, watcher, url, expected_change=True):
        """Custom assertion for URL change detection"""
        changed, diff = watcher.check_url(url)

        if expected_change:
            self.assertTrue(changed, f"Expected {url} to have changed")
            self.assertIsNotNone(diff, "Expected diff content for changed URL")
        else:
            self.assertFalse(changed, f"Expected {url} to be unchanged")

    def assertSMSConfigured(self, notifier):
        """Custom assertion for SMS configuration"""
        self.assertTrue(notifier.is_configured(), "SMS notifier not properly configured")
        self.assertIsNotNone(notifier.topic_arn, "Topic ARN not set")
        self.assertIsNotNone(notifier.sns_client, "SNS client not initialized")
```

### Test Data Generators

```python
def generate_test_html(title="Test Page", content="Test content"):
    """Generate test HTML content"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>{title}</title></head>
    <body>
        <h1>{title}</h1>
        <p>{content}</p>
    </body>
    </html>
    """

def generate_test_json_response(data=None):
    """Generate test JSON response"""
    default_data = {
        "id": 123,
        "timestamp": "2025-07-29T16:45:32Z",
        "status": "ok"
    }
    return json.dumps(data or default_data, indent=2)
```

## Continuous Integration

### GitHub Actions Example

Create `.github/workflows/tests.yml`:

```yaml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.7, 3.8, 3.9, '3.10', '3.11']

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v3
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install coverage

    - name: Run tests with coverage
      run: |
        coverage run -m unittest discover -s . -p "test_*.py"
        coverage report
        coverage xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
```

### Pre-commit Hooks

Install pre-commit:
```bash
pip install pre-commit
```

Create `.pre-commit-config.yaml`:
```yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run tests
        entry: python -m unittest discover -s . -p "test_*.py"
        language: system
        pass_filenames: false
        always_run: true
```

Install hooks:
```bash
pre-commit install
```

### Test Commands Summary

```bash
# Quick test run
python test_sms_notifications.py

# Comprehensive testing
python -m unittest discover -s . -p "test_*.py" -v

# With coverage
coverage run -m unittest discover -s . -p "test_*.py"
coverage report
coverage html

# Specific test debugging
python -m unittest test_sms_notifications.TestSMSNotifier.test_send_notification_success -v

# Performance testing
python -m unittest test_performance.TestPerformance -v
```

This testing guide provides comprehensive coverage of testing practices for the URL Watcher project, ensuring reliability and maintainability of the codebase.
