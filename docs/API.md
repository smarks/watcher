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
notifier = SMSNotifier(phone_number="+1234567890", api_key="your_textbelt_key")
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
    changed, diff = watcher.check_url("https://example.com")
    if changed:
        print("Content has changed!")
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
- Runs indefinitely until interrupted with Ctrl+C
- Uses randomized intervals to avoid detection as automated scraping
- Prints status updates for each check
- Sends SMS notifications if configured

**Example:**
```python
from sms_notifier import create_notifier_from_env

watcher = URLWatcher(sms_notifier=create_notifier_from_env())

try:
    watcher.watch_continuously("https://example.com", min_interval=30, max_interval=120)
except KeyboardInterrupt:
    print("Monitoring stopped")
```

---

## SMSNotifier Class

### Overview
The `SMSNotifier` class handles SMS notifications using the TextBelt API service.

### Constructor

```python
SMSNotifier(phone_number=None, api_key=None)
```

**Parameters:**
- `phone_number` (str, optional): Phone number in E.164 format (e.g., "+1234567890")
- `api_key` (str, optional): TextBelt API key

If parameters are not provided, the class will attempt to read from environment variables:
- `SMS_PHONE_NUMBER`: Target phone number
- `TEXTBELT_API_KEY`: TextBelt API key

**Example:**
```python
from sms_notifier import SMSNotifier

# Using explicit credentials
notifier = SMSNotifier(
    phone_number="+1234567890",
    api_key="your_textbelt_api_key"
)

# Using environment variables
notifier = SMSNotifier()  # Reads from environment
```

### Methods

#### `is_configured()`

Checks if the SMS notifier is properly configured with required credentials.

**Returns:**
- `bool`: True if phone number and API key are available, False otherwise

**Example:**
```python
notifier = SMSNotifier()
if notifier.is_configured():
    print("SMS notifications ready")
else:
    print("SMS not configured - set SMS_PHONE_NUMBER and TEXTBELT_API_KEY")
```

#### `send_notification(url, message, subject=None)`

Sends an SMS notification about a URL change.

**Parameters:**
- `url` (str): The URL that changed
- `message` (str): Description of the changes (will be filtered for TextBelt compatibility)
- `subject` (str, optional): Not used with TextBelt (legacy parameter)

**Returns:**
- `bool`: True if SMS was sent successfully, False otherwise

**Example:**
```python
notifier = SMSNotifier(phone_number="+1234567890", api_key="your_key")

success = notifier.send_notification(
    "https://example.com", 
    "Content changes detected"
)

if success:
    print("SMS notification sent!")
else:
    print("Failed to send SMS")
```

#### `test_notification()`

Sends a test SMS to verify configuration.

**Returns:**
- `dict`: Test results with the following keys:
  - `success` (bool): Whether the test succeeded
  - `text_id` (str): TextBelt message ID if successful
  - `error` (str): Error message if failed
  - `details` (dict): Additional information

**Example:**
```python
notifier = SMSNotifier()
result = notifier.test_notification()

if result["success"]:
    print(f"Test SMS sent! Message ID: {result['text_id']}")
else:
    print(f"Test failed: {result['error']}")
```

---

## Utility Functions

### `create_notifier_from_env(load_dotenv=True)`

Creates an SMS notifier using environment variables.

**Parameters:**
- `load_dotenv` (bool): Whether to load variables from .env file (default: True)

**Environment Variables:**
- `SMS_PHONE_NUMBER`: Phone number in E.164 format
- `TEXTBELT_API_KEY`: TextBelt API key

**Returns:**
- `SMSNotifier`: Configured notifier instance

**Example:**
```python
import os
from sms_notifier import create_notifier_from_env

# Set environment variables
os.environ['SMS_PHONE_NUMBER'] = '+1234567890'
os.environ['TEXTBELT_API_KEY'] = 'your_api_key'

# Create notifier
notifier = create_notifier_from_env()

if notifier.is_configured():
    print("SMS notifier ready")
```

---

## Error Handling

### Common Exceptions

#### Network Errors
```python
try:
    changed, diff = watcher.check_url("https://example.com")
except Exception as e:
    if "Failed to fetch URL" in str(e):
        print(f"Network error: {e}")
    else:
        print(f"Other error: {e}")
```

#### SMS Errors
```python
notifier = SMSNotifier()
if not notifier.is_configured():
    print("SMS not configured properly")
    
result = notifier.send_notification("https://example.com", "test")
if not result:
    print("SMS sending failed - check logs for details")
```

### Logging

The modules use Python's logging system. Enable INFO level logging to see operational details:

```python
import logging
logging.basicConfig(level=logging.INFO)

# Now SMS operations will show detailed logs
notifier.send_notification("https://example.com", "test message")
```

---

## Configuration Files

### .env File Format
```
# TextBelt Configuration
SMS_PHONE_NUMBER=+1234567890
TEXTBELT_API_KEY=your_api_key_here
```

### Cache File Format
The URL cache is stored as JSON:
```json
{
  "https://example.com": {
    "content": "<!DOCTYPE html>...",
    "hash": "sha256_hash_of_content",
    "last_checked": "2023-10-01T12:00:00.000000"
  }
}
```

---

## Performance Notes

- **Randomized Intervals**: Continuous monitoring uses random intervals to avoid detection
- **Content Hashing**: Quick hash comparison before expensive diff generation  
- **Efficient Storage**: Only stores necessary data in cache files
- **SMS Rate Limiting**: TextBelt has rate limits - avoid excessive notifications