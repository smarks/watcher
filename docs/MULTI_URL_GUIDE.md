# Multi-URL Watcher Usage Guide

## Quick Start

### 1. Basic Setup
```bash
# Copy sample environment file and configure SMS
cp sample.env .env
# Edit .env with your SMS credentials and phone number

# Test SMS configuration (optional but recommended)
python test_clicksend_sms_notifier.py
```

### 2. Single URL Monitoring
```bash
# Monitor one URL with default 60-second interval
python multi_url_watcher.py https://example.com --sms

# Monitor with custom interval (5 minutes = 300 seconds)
python multi_url_watcher.py https://api.github.com/user --interval 300 --sms
```

### 3. Multiple URL Monitoring
```bash
# Create configuration file (or use provided examples)
python multi_url_watcher.py urls.json --sms
# This creates a sample urls.json if it doesn't exist

# Use pre-made example configurations
python multi_url_watcher.py examples/api_monitoring.json --sms
```

## Configuration Examples

### Basic Configuration (`urls.json`)
```json
[
  {
    "url": "https://httpbin.org/uuid",
    "interval": 30
  },
  {
    "url": "https://example.com",
    "interval": 300
  }
]
```

### Advanced Configuration with Comments
```json
[
  {
    "url": "https://api.github.com/repos/python/cpython/releases/latest",
    "interval": 3600,
    "description": "Python releases - hourly checks"
  },
  {
    "url": "https://status.github.com/api/status.json",
    "interval": 300,
    "description": "GitHub status - every 5 minutes"
  },
  {
    "url": "https://news.ycombinator.com",
    "interval": 900,
    "description": "Hacker News - every 15 minutes"
  }
]
```

## Understanding the Output

### Normal Operation
```
Starting monitoring of 3 URLs
============================================================
📍 https://api.github.com/repos/python/cpython/releases/latest
   Check interval: 3600 seconds
📍 https://status.github.com/api/status.json
   Check interval: 300 seconds
📍 https://news.ycombinator.com
   Check interval: 900 seconds
============================================================
Press Ctrl+C to stop

[2025-09-05 17:45:00] Checking: https://status.github.com/api/status.json
   ⚪ No changes

Next check (https://status.github.com/...) in: 04:58
```

### When Content Changes
```
[2025-09-05 17:50:00] Checking: https://api.github.com/releases/latest
   ✅ CHANGED!
   Diff preview: --- https://api.github.com/releases/latest (previous)
+++ https://api.github.com/releases/latest (current)
@@ -1,5 +1,5 @@
 {
   "tag_name": "v3.12.0",
-  "name": "Python 3.12.0",
+  "name": "Python 3.12.1",
...

[SMS] ✓ SMS sent successfully via ClickSend
```

### When Sites Go Down
```
[2025-09-05 18:00:00] Checking: https://example.com
   🔴 UNREACHABLE: Connection failed: Connection timed out

🔴 ALERT: https://example.com is UNREACHABLE!
Error: Connection failed: Connection timed out

[SMS] ✓ SMS sent successfully via ClickSend (Unreachable alert)
```

### When Sites Recover
```
[2025-09-05 18:15:00] Checking: https://example.com
   ✅ CHANGED!

🟢 RECOVERED: https://example.com is back online!
Downtime: 0:15:00

[SMS] ✓ SMS sent successfully via ClickSend (Recovery alert)
```

### Final Statistics
```
Stopping monitoring...

Stats:
============================================================
📊 https://api.github.com/repos/python/cpython/releases/latest
   Total checks: 24
   Last change: 2025-09-05

📊 https://status.github.com/api/status.json
   Total checks: 156
   Last change: Never

📊 https://news.ycombinator.com
   Total checks: 67
   Last change: 2025-09-04
============================================================
```

## SMS Notification Examples

### Content Change Notification
```
WEBSITE CHANGE DETECTED
Time: 2025-09-05 17:50:00
URL: https://api.github.com/releases/latest

Changes:
--- https://api.github.com/releases/latest (previous)
+++ https://api.github.com/releases/latest (current)
@@ -3,7 +3,7 @@
   "tag_name": "v3.12.0",
-  "name": "Python 3.12.0",
+  "name": "Python 3.12.1",
   "published_at": "2025-09-05T17:45:00Z"
...
[truncated]
```

### Site Down Alert
```
🔴 SITE UNREACHABLE

URL: https://example.com
Error: Connection failed: Connection timed out
Time: 2025-09-05 18:00:00
```

### Site Recovery Alert
```
🟢 SITE RECOVERED

URL: https://example.com
Downtime: 0:15:00
Time: 2025-09-05 18:15:00
```

## Recommended Intervals

| Content Type | Interval | Reasoning |
|-------------|----------|-----------|
| **News sites** | 15-30 min | Frequently updated content |
| **API releases** | 1-2 hours | Infrequent but important updates |
| **Service status pages** | 5-15 min | Need quick outage detection |
| **Personal blogs** | 4-24 hours | Infrequent updates |
| **Social media APIs** | 10-30 min | Moderate update frequency |
| **Weather APIs** | 1-6 hours | Depends on use case |

## Troubleshooting

### No SMS Notifications
1. Check `.env` file has correct credentials
2. Test SMS setup: `python test_clicksend_sms_notifier.py`
3. Verify phone number format: `+1234567890`
4. Check logs for `[SMS]` messages

### High Memory Usage
- Reduce number of concurrent URLs
- Increase check intervals
- The watcher keeps content in memory for diff generation

### Network Errors
- The watcher automatically retries failed requests (3 attempts)
- Temporary network issues won't trigger false change alerts
- Check logs for retry attempts: `[SMS] Attempt 2/3 failed`

### Configuration Errors
- Validate JSON: `python -m json.tool urls.json`
- Check required fields: `url` and `interval`
- Intervals are in seconds (60 = 1 minute, 3600 = 1 hour)

## Advanced Usage

### Run as Background Service
```bash
# Using nohup (Linux/macOS)
nohup python multi_url_watcher.py urls.json --sms > watcher.log 2>&1 &

# Using screen (Linux/macOS)
screen -S watcher python multi_url_watcher.py urls.json --sms

# Using systemd (Linux) - create service file
sudo systemctl start url-watcher
```

### Monitoring Large Numbers of URLs
- Keep intervals reasonable (minimum 30 seconds)
- Group similar URLs by check frequency
- Monitor system resources (CPU/memory)
- Consider splitting into multiple configuration files

### Custom Headers / Authentication
The current version doesn't support custom headers. For APIs requiring authentication, consider:
1. Using API keys in the URL (if supported)
2. Monitoring public endpoints that reflect the authenticated state
3. Extending the code to support custom headers (see Contributing section)

## Example Use Cases

### 1. Software Release Monitoring
Monitor GitHub releases for your dependencies:
```json
[
  {"url": "https://api.github.com/repos/python/cpython/releases/latest", "interval": 7200},
  {"url": "https://api.github.com/repos/nodejs/node/releases/latest", "interval": 7200},
  {"url": "https://api.github.com/repos/microsoft/vscode/releases/latest", "interval": 3600}
]
```

### 2. Service Health Monitoring
Monitor your services and dependencies:
```json
[
  {"url": "https://status.github.com/api/status.json", "interval": 300},
  {"url": "https://status.slack.com/api/v2.0.0/current", "interval": 300},
  {"url": "https://your-app.com/health", "interval": 60}
]
```

### 3. Content Change Monitoring
Monitor competitor sites or news sources:
```json
[
  {"url": "https://competitor.com/pricing", "interval": 86400},
  {"url": "https://news.ycombinator.com", "interval": 1800},
  {"url": "https://www.reddit.com/r/programming/.rss", "interval": 3600}
]
```

## Contributing

The multi-URL watcher is designed to be extensible. Common enhancements:

1. **Custom Headers**: Add authentication support
2. **Webhook Notifications**: Support Discord/Slack in addition to SMS
3. **Content Filtering**: Monitor specific page sections using CSS selectors
4. **Database Storage**: Replace JSON cache with database for better performance
5. **Web Dashboard**: Add web interface for configuration and monitoring

See the test suite (`test_multi_url_watcher.py`) for examples of how the code is structured and tested.
