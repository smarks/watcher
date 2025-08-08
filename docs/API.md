# API Documentation

## URLWatcher Class

### Overview
The `URLWatcher` class is the core component for monitoring URL content changes.

### Constructor

```python
URLWatcher(storage_file="url_cache.json", sms_notifier=None)
```

**Parameters:**
- `storage_file` (str): Path to the JSON file for caching URL content. Defaults to "url_cache.json"
- `sms_notifier` (SMSNotifier, optional): Instance of SMSNotifier for sending SMS alerts

**Example:**
```python
from url_watcher import URLWatcher
from sms_notifier import SMSNotifier

# Basic usage
watcher = URLWatcher()

# With custom cache file
watcher = URLWatcher(storage_file="custom_cache.json")

# With SMS notifications
notifier = SMSNotifier(topic_arn="arn:aws:sns:us-east-1:123456789012:topic")
watcher = URLWatcher(sms_notifier=notifier)
```

### Methods

#### `check_url(url)`

Performs a single check of the specified URL and compares it with previously cached content.

**Parameters:**
- `url` (str): The URL to monitor

**Returns:**
- `tuple`: (changed: bool, difference: str or None)
  - `changed`: True if content has changed since last check, False otherwise
  - `difference`: Unified diff string showing changes, or None if no changes

**Raises:**
- `Exception`: If URL cannot be fetched (network errors, invalid URL, etc.)

**Example:**
```python
watcher = URLWatcher()

try:
    changed, diff = watcher.check_url("https://httpbin.org/uuid")
    if changed:
        print("Content changed!")
        print(diff)
    else:
        print("No changes detected")
except Exception as e:
    print(f"Error checking URL: {e}")
```

#### `watch_continuously(url, min_interval=60, max_interval=300)`

Continuously monitors a URL with random intervals between checks.

**Parameters:**
- `url` (str): The URL to monitor
- `min_interval` (int): Minimum seconds between checks (default: 60)
- `max_interval` (int): Maximum seconds between checks (default: 300)

**Behavior:**
- Runs indefinitely until interrupted (Ctrl+C)
- Uses random intervals between min_interval and max_interval
- Prints status messages with timestamps
- Gracefully handles network errors and continues monitoring

**Example:**
```python
watcher = URLWatcher()

# Monitor with default intervals (1-5 minutes)
watcher.watch_continuously("https://example.com")

# Monitor with custom intervals (30-120 seconds)
watcher.watch_continuously("https://example.com", 30, 120)
```

### Private Methods

#### `_load_cache()`
Loads URL content cache from the storage file.

#### `_save_cache()`
Saves URL content cache to the storage file.

#### `_fetch_url_content(url)`
Fetches content from the specified URL using requests library.

#### `_get_content_hash(content)`
Generates SHA256 hash of content for quick comparison.

#### `_generate_diff(old_content, new_content, url)`
Generates unified diff between old and new content.

---

## SMSNotifier Class

### Overview
The `SMSNotifier` class handles SMS notifications via AWS SNS service.

### Constructor

```python
SMSNotifier(topic_arn=None, aws_access_key_id=None, 
           aws_secret_access_key=None, region_name='us-east-1')
```

**Parameters:**
- `topic_arn` (str, optional): AWS SNS Topic ARN. Can be set via SNS_TOPIC_ARN environment variable
- `aws_access_key_id` (str, optional): AWS access key ID. Can be set via AWS_ACCESS_KEY_ID environment variable
- `aws_secret_access_key` (str, optional): AWS secret access key. Can be set via AWS_SECRET_ACCESS_KEY environment variable
- `region_name` (str): AWS region name. Defaults to 'us-east-1'

**Example:**
```python
from sms_notifier import SMSNotifier

# Using explicit credentials
notifier = SMSNotifier(
    topic_arn="arn:aws:sns:us-east-1:123456789012:url-watcher-notifications",
    aws_access_key_id="AKIAIOSFODNN7EXAMPLE",
    aws_secret_access_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
)

# Using environment variables or IAM role
notifier = SMSNotifier(topic_arn="arn:aws:sns:us-east-1:123456789012:topic")

# Using environment variables for everything
notifier = SMSNotifier()  # Reads from environment
```

### Methods

#### `is_configured()`

Checks if SMS notifications are properly configured.

**Returns:**
- `bool`: True if both SNS client and topic ARN are available

**Example:**
```python
notifier = SMSNotifier()
if notifier.is_configured():
    print("SMS notifications ready")
else:
    print("SMS configuration incomplete")
```

#### `send_notification(url, message, subject=None)`

Sends SMS notification about URL change.

**Parameters:**
- `url` (str): The URL that changed
- `message` (str): Change description/diff content
- `subject` (str, optional): Message subject line

**Returns:**
- `bool`: True if notification sent successfully, False otherwise

**Message Format:**
```
URL CHANGE DETECTED
Time: 2025-07-29 16:45:32
URL: https://example.com

Changes: [first 100 characters of diff]...
```

**Example:**
```python
notifier = SMSNotifier(topic_arn="arn:aws:sns:us-east-1:123456789012:topic")

success = notifier.send_notification(
    url="https://example.com",
    message="Content changed from 'Hello' to 'Hi'",
    subject="Website Update"
)

if success:
    print("SMS sent successfully")
else:
    print("Failed to send SMS")
```

#### `test_notification()`

Sends a test SMS to verify configuration.

**Returns:**
- `dict`: Test results with the following structure:
  ```python
  {
      'success': bool,           # True if test passed
      'message_id': str,         # AWS message ID (if successful)
      'error': str,              # Error message (if failed)
      'error_code': str,         # AWS error code (if AWS error)
      'details': dict            # Additional configuration details
  }
  ```

**Example:**
```python
notifier = SMSNotifier()
result = notifier.test_notification()

if result['success']:
    print(f"Test SMS sent! Message ID: {result['message_id']}")
else:
    print(f"Test failed: {result['error']}")
```

---

## Utility Functions

### `create_notifier_from_env()`

Creates an SMSNotifier instance using environment variables.

**Environment Variables:**
- `SNS_TOPIC_ARN`: AWS SNS Topic ARN (required)
- `AWS_ACCESS_KEY_ID`: AWS access key ID (required)
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key (required)  
- `AWS_REGION`: AWS region (optional, defaults to us-east-1)

**Returns:**
- `SMSNotifier`: Configured SMS notifier instance

**Example:**
```python
import os
from sms_notifier import create_notifier_from_env

# Set environment variables
os.environ['SNS_TOPIC_ARN'] = 'arn:aws:sns:us-east-1:123456789012:topic'
os.environ['AWS_ACCESS_KEY_ID'] = 'AKIAIOSFODNN7EXAMPLE'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'

# Create notifier
notifier = create_notifier_from_env()

if notifier.is_configured():
    print("SMS notifier ready")
```

---

## Data Structures

### Cache File Format

The URL cache is stored as JSON with the following structure:

```json
{
  "https://example.com": {
    "content": "<!DOCTYPE html>\n<html>...",
    "hash": "a1b2c3d4e5f6...",
    "last_checked": "2025-07-29T16:45:32.123456"
  },
  "https://another-site.com": {
    "content": "<html>...",
    "hash": "f6e5d4c3b2a1...",
    "last_checked": "2025-07-29T16:30:15.789012"
  }
}
```

**Fields:**
- `content`: Full HTML content of the page
- `hash`: SHA256 hash for quick comparison
- `last_checked`: ISO format timestamp of last check

### Error Handling

#### URLWatcher Errors

**Network Errors:**
```python
try:
    changed, diff = watcher.check_url("https://invalid-url.com")
except Exception as e:
    print(f"Network error: {e}")
    # Continue with other URLs or retry logic
```

**Common Error Types:**
- `requests.exceptions.ConnectionError`: Network connectivity issues
- `requests.exceptions.Timeout`: Request timeout
- `requests.exceptions.HTTPError`: HTTP error responses (404, 500, etc.)
- `json.JSONDecodeError`: Cache file corruption

#### SMSNotifier Errors

**AWS SNS Errors:**
```python
from botocore.exceptions import ClientError

notifier = SMSNotifier()
try:
    success = notifier.send_notification(url, message)
except ClientError as e:
    error_code = e.response['Error']['Code']
    if error_code == 'InvalidParameter':
        print("Invalid topic ARN or phone number")
    elif error_code == 'NotFound':
        print("SNS topic not found")
    else:
        print(f"AWS error: {e}")
```

**Common AWS Error Codes:**
- `InvalidParameter`: Invalid topic ARN, phone number, or message
- `NotFound`: SNS topic doesn't exist
- `InvalidClientTokenId`: Invalid AWS credentials
- `AccessDenied`: Insufficient permissions

---

## Integration Examples

### Basic Monitoring Script

```python
#!/usr/bin/env python3
import sys
from url_watcher import URLWatcher

def main():
    if len(sys.argv) != 2:
        print("Usage: python monitor.py <URL>")
        sys.exit(1)
    
    url = sys.argv[1]
    watcher = URLWatcher()
    
    try:
        changed, diff = watcher.check_url(url)
        if changed:
            print(f"✅ {url} has changed!")
            print(diff)
            return 0  # Exit code for "changed"
        else:
            print(f"❌ {url} - no changes")
            return 1  # Exit code for "no changes"
    except Exception as e:
        print(f"❌ Error checking {url}: {e}")
        return 2  # Exit code for "error"

if __name__ == "__main__":
    sys.exit(main())
```

### Monitoring with SMS Alerts

```python
#!/usr/bin/env python3
import logging
from url_watcher import URLWatcher
from sms_notifier import create_notifier_from_env

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    urls = [
        "https://example.com",
        "https://httpbin.org/uuid",
        "https://api.github.com/zen"
    ]
    
    # Setup SMS notifications
    notifier = create_notifier_from_env()
    if not notifier.is_configured():
        logging.warning("SMS notifications not configured")
        notifier = None
    
    watcher = URLWatcher(sms_notifier=notifier)
    
    # Check all URLs
    for url in urls:
        try:
            changed, diff = watcher.check_url(url)
            if changed:
                logging.info(f"Change detected: {url}")
                print(f"✅ {url} changed!")
                if diff:
                    print(diff[:500] + "..." if len(diff) > 500 else diff)
            else:
                logging.info(f"No changes: {url}")
        except Exception as e:
            logging.error(f"Error checking {url}: {e}")

if __name__ == "__main__":
    main()
```

### Custom Notification Handler

```python
import smtplib
from email.mime.text import MIMEText
from url_watcher import URLWatcher

class EmailNotifier:
    def __init__(self, smtp_server, username, password, to_email):
        self.smtp_server = smtp_server
        self.username = username
        self.password = password
        self.to_email = to_email
    
    def send_notification(self, url, message):
        try:
            msg = MIMEText(f"URL {url} has changed:\n\n{message}")
            msg['Subject'] = f'URL Change Alert: {url}'
            msg['From'] = self.username
            msg['To'] = self.to_email
            
            with smtplib.SMTP(self.smtp_server, 587) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            return True
        except Exception as e:
            print(f"Email notification failed: {e}")
            return False

# Custom watcher with email notifications
class EmailURLWatcher(URLWatcher):
    def __init__(self, email_notifier, **kwargs):
        super().__init__(**kwargs)
        self.email_notifier = email_notifier
    
    def check_url(self, url):
        changed, diff = super().check_url(url)
        if changed and self.email_notifier:
            self.email_notifier.send_notification(url, diff)
        return changed, diff

# Usage
email_notifier = EmailNotifier(
    smtp_server="smtp.gmail.com",
    username="your-email@gmail.com", 
    password="your-app-password",
    to_email="alerts@example.com"
)

watcher = EmailURLWatcher(email_notifier=email_notifier)
watcher.watch_continuously("https://example.com")
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SNS_TOPIC_ARN` | AWS SNS Topic ARN for SMS | None | For SMS |
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID | None | For SMS |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key | None | For SMS |
| `AWS_REGION` | AWS Region | us-east-1 | No |

### Command Line Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `URL` | URL to monitor | `https://example.com` |
| `--continuous` | Enable continuous monitoring | `--continuous` |
| `--sms` | Enable SMS notifications | `--sms` |

### Cache File Configuration

The cache file location can be customized:

```python
# Custom cache location
watcher = URLWatcher(storage_file="/path/to/my/cache.json")

# Temporary cache (deleted on exit)
import tempfile
import os

temp_cache = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
watcher = URLWatcher(storage_file=temp_cache.name)

# Clean up when done
os.unlink(temp_cache.name)
```

---

## Performance Considerations

### Memory Usage

- Cache file grows with number of monitored URLs
- Each URL stores full page content in memory
- Large pages (>1MB) may impact performance

**Optimization tips:**
- Regularly clean old cache entries
- Monitor memory usage with large sites
- Consider using content hashing only for very large pages

### Network Performance

- HTTP requests use 10-second timeout by default
- No connection pooling for single URL checks
- Continuous monitoring reuses URLWatcher instance

**Best practices:**
- Use appropriate check intervals for site update frequency
- Implement exponential backoff for failed requests
- Consider using HEAD requests for large files (requires custom implementation)

### AWS SNS Limits

- SMS: 100 messages per second (burst), sustained rate varies by region
- Topic publish: 300 TPS per region
- Message size: 1600 characters max

**Rate limiting considerations:**
- SMS notifications are sent synchronously
- Failed SMS doesn't stop URL monitoring
- Consider batching notifications for multiple URL changes