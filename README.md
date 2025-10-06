# URL Watcher

A Python tool that monitors websites for content changes and sends SMS notifications via ClickSend.

## Features

- **Single URL Monitoring**: Monitor one URL with simple command-line interface
- **Multi-URL Monitoring**: Monitor multiple URLs with individual check intervals
- **SMS Notifications**: Get notified via ClickSend when content changes
- **Change Detection**: SHA256-based content hashing with diff output
- **Resilience**: Automatic retry logic with exponential backoff (multi-URL mode)
- **Continuous Monitoring**: Background monitoring with randomized intervals
- **Comprehensive Logging**: Detailed logs of all checks and notifications

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
pip install clicksend-client  # For SMS notifications
```

### 2. Configure SMS (Optional)

Create a `.env` file in the project root:

```bash
SMS_PHONE_NUMBER="+19786341135"
CLICKSEND_USERNAME="your_email@example.com"
CLICKSEND_API_KEY="your-api-key-here"
```

Get your ClickSend credentials at: https://dashboard.clicksend.com/

### 3. Monitor a URL

**Single URL - One-time check:**
```bash
python src/url_watcher.py https://example.com --sms
```

**Single URL - Continuous monitoring:**
```bash
python src/url_watcher.py https://example.com --continuous --sms
```

**Multi-URL monitoring with JSON config:**
```bash
python src/multi_url_watcher.py urls.json --sms
```

**Multi-URL - Single URL with custom interval:**
```bash
python src/multi_url_watcher.py https://example.com --interval 60 --sms
```

## Usage

### Single URL Watcher

```bash
python src/url_watcher.py <URL> [--continuous] [--sms]
```

**Options:**
- `--continuous` - Monitor continuously with randomized intervals (300-600 seconds)
- `--sms` - Send SMS notifications when changes detected

**Examples:**
```bash
# Check once
python src/url_watcher.py https://example.com

# Continuous monitoring with SMS
python src/url_watcher.py https://example.com --continuous --sms

# Run in background with logging
nohup python src/url_watcher.py https://example.com --continuous --sms 2>&1 | tee -a url_watcher.log &
```

### Multi-URL Watcher

```bash
python src/multi_url_watcher.py <config.json|URL> [--interval SECONDS] [--sms]
```

**Options:**
- `--interval SECONDS` - Check interval (only when using single URL, default: 300)
- `--sms` - Send SMS notifications

**Examples:**
```bash
# Monitor multiple URLs from config file
python src/multi_url_watcher.py urls.json --sms

# Monitor single URL with 60-second interval
python src/multi_url_watcher.py https://example.com --interval 60 --sms

# Run in background
nohup python src/multi_url_watcher.py urls.json --sms 2>&1 | tee -a multi_watcher.log &
```

## Configuration

### Multi-URL JSON Config

Create a `urls.json` file with your URLs and check intervals:

```json
[
  {
    "url": "https://example.com",
    "interval": 300
  },
  {
    "url": "https://api.github.com/repos/python/cpython/releases/latest",
    "interval": 3600
  },
  {
    "url": "https://news.ycombinator.com",
    "interval": 600
  }
]
```

**Configuration options:**
- `url` (required) - The URL to monitor
- `interval` (required) - Check interval in seconds

**Common intervals:**
- `60` - Every minute
- `300` - Every 5 minutes
- `600` - Every 10 minutes
- `1800` - Every 30 minutes
- `3600` - Every hour
- `86400` - Every 24 hours

### Environment Variables

Set these in `.env` file or export them:

```bash
# Required for SMS notifications
SMS_PHONE_NUMBER="+19786341135"        # Your phone number with country code
CLICKSEND_USERNAME="user@example.com"  # ClickSend username
CLICKSEND_API_KEY="YOUR-API-KEY"       # ClickSend API key

# Optional
CLICKSEND_SOURCE="URLWatcher"          # Sender name (default: URLWatcher)
```

### Background Monitoring

Run continuously in the background:

```bash
# With screen and file logging
nohup python src/url_watcher.py https://example.com --continuous --sms 2>&1 | tee -a url_watcher.log &

# View live logs
tail -f url_watcher.log

# Check if running
ps aux | grep url_watcher

# Stop the process
pkill -f url_watcher.py
```

**Redirect explanation:**
- `2>&1` - Redirects stderr to stdout (captures all output)
- `| tee -a file.log` - Writes to both screen and log file (appends)
- `&` - Runs in background

## Testing

### Run All Tests

```bash
python -m pytest src/test/ -v
```

### Test SMS Integration

**Verify setup (no SMS sent):**
```bash
pytest src/test/test_sms_integration.py::TestSMSIntegration::test_verify_setup -v
```

**Send actual test SMS:**
```bash
pytest src/test/test_sms_integration.py::TestSMSIntegration::test_send_test_sms -v
```

**Interactive mode (prompts before sending):**
```bash
python src/test/test_sms_integration.py --interactive
```

See `src/test/SMS_TESTING_GUIDE.md` for detailed testing instructions.

## Features by Watcher Type

### Single URL Watcher (`url_watcher.py`)
- Simple command-line interface
- One URL at a time
- Continuous or one-time checks
- Randomized intervals (300-600s) when continuous
- SMS notifications via ClickSend

### Multi-URL Watcher (`multi_url_watcher.py`)
All features from Single URL Watcher, plus:
- Monitor multiple URLs simultaneously
- Individual check intervals per URL
- Automatic retry with exponential backoff (5s, 10s, 20s)
- Distinguishes network failures from content changes
- SMS alerts when sites go down and recover
- Parallel checking when multiple URLs are due
- Per-URL statistics (check count, last change time)
- Recovery notifications

## Troubleshooting

### SMS not received

1. **Check ClickSend dashboard**: https://dashboard.clicksend.com/sms/history
2. **Verify credentials** in `.env` file
3. **Check phone number format**: Must include country code (e.g., `+19786341135`)
4. **Run verification test**:
   ```bash
   pytest src/test/test_sms_integration.py::TestSMSIntegration::test_verify_setup -v
   ```

### No changes detected

- First check establishes baseline (no notification sent)
- Subsequent checks compare against cached content
- Cache stored in `url_cache.json` (single) or `multi_url_cache.json` (multi)

### Import errors

Run from project root directory:
```bash
python src/url_watcher.py https://example.com
```

Not from src directory:
```bash
cd src
python url_watcher.py https://example.com  # May cause import errors
```

## Requirements

- Python 3.9+
- ClickSend account (for SMS notifications)
- Internet connection

## License

MIT
