# Usage Examples and Tutorials

## Table of Contents

- [Basic Examples](#basic-examples)
- [Advanced Usage](#advanced-usage)
- [Real-World Scenarios](#real-world-scenarios)
- [Integration Examples](#integration-examples)
- [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Basic Examples

### 1. Simple URL Check

Check a single URL once and see if it has changed:

```bash
python url_watcher.py https://httpbin.org/uuid
```

**Expected Output (First Run):**
```
❌ No changes detected
First time checking this URL - no previous content to compare
```

**Expected Output (Subsequent Runs):**
```
✅ Content has CHANGED!

Difference:
--- https://httpbin.org/uuid (previous)
+++ https://httpbin.org/uuid (current)
@@ -3,5 +3,5 @@
   "origin": "203.0.113.12",
-  "url": "https://httpbin.org/uuid",
-  "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
+  "url": "https://httpbin.org/uuid",
+  "uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
 }
```

### 2. Continuous Monitoring

Monitor a URL continuously with random intervals:

```bash
python url_watcher.py https://httpbin.org/uuid --continuous
```

**Expected Output:**
```
Starting continuous monitoring of: https://httpbin.org/uuid
Check interval: 60-300 seconds
Press Ctrl+C to stop

[2025-07-29 16:45:32] Checking URL...
✅ Content has CHANGED!

Difference:
--- https://httpbin.org/uuid (previous)
+++ https://httpbin.org/uuid (current)
@@ -3,5 +3,5 @@
   "origin": "203.0.113.12",
-  "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
+  "uuid": "550e8400-e29b-41d4-a716-446655440000"
 }

Next check in 143 seconds...

[2025-07-29 16:48:15] Checking URL...
✅ Content has CHANGED!
...
```

### 3. Local Testing

Set up a local test environment to see URL Watcher in action:

**Terminal 1 - Start Local Server:**
```bash
python -m http.server 8080
```

**Terminal 2 - Monitor Local Server:**
```bash
python url_watcher.py http://localhost:8080 --continuous
```

**Terminal 3 - Make Changes:**
```bash
# Edit index.html to see changes detected
echo "<h1>Updated content</h1>" >> index.html
```

## Advanced Usage

### 4. Custom Check Intervals

Create a script with custom monitoring intervals:

```python
#!/usr/bin/env python3
"""
Custom monitoring script with short intervals for testing
"""
from url_watcher import URLWatcher

def main():
    watcher = URLWatcher()

    # Monitor every 10-30 seconds (good for testing)
    watcher.watch_continuously(
        "http://localhost:8080",
        min_interval=10,
        max_interval=30
    )

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python custom_monitor.py
```

### 5. Multiple URL Monitoring

Monitor multiple URLs in sequence:

```python
#!/usr/bin/env python3
"""
Monitor multiple URLs and report changes
"""
import time
from url_watcher import URLWatcher

def monitor_multiple_urls(urls, interval=60):
    watcher = URLWatcher()

    while True:
        print(f"\n=== Checking {len(urls)} URLs at {time.strftime('%H:%M:%S')} ===")

        for url in urls:
            try:
                changed, diff = watcher.check_url(url)
                if changed:
                    print(f"✅ CHANGED: {url}")
                    if diff:
                        # Show first 200 chars of diff
                        short_diff = diff[:200] + "..." if len(diff) > 200 else diff
                        print(f"   {short_diff}")
                else:
                    print(f"❌ No change: {url}")
            except Exception as e:
                print(f"❌ ERROR: {url} - {e}")

        print(f"\nSleeping for {interval} seconds...")
        time.sleep(interval)

if __name__ == "__main__":
    urls_to_monitor = [
        "https://httpbin.org/uuid",
        "https://api.github.com/zen",
        "https://httpbin.org/delay/1"
    ]

    monitor_multiple_urls(urls_to_monitor, interval=30)
```

### 6. Content Filtering

Monitor specific parts of a webpage:

```python
#!/usr/bin/env python3
"""
Monitor only specific content using BeautifulSoup
"""
import requests
from bs4 import BeautifulSoup
from url_watcher import URLWatcher

class FilteredURLWatcher(URLWatcher):
    def __init__(self, css_selector=None, **kwargs):
        super().__init__(**kwargs)
        self.css_selector = css_selector

    def _fetch_url_content(self, url):
        """Override to filter content using CSS selector"""
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        if self.css_selector:
            soup = BeautifulSoup(response.text, 'html.parser')
            elements = soup.select(self.css_selector)
            return '\n'.join(str(el) for el in elements)

        return response.text

# Usage examples
if __name__ == "__main__":
    # Monitor only H1 tags
    h1_watcher = FilteredURLWatcher(css_selector="h1")
    changed, diff = h1_watcher.check_url("https://example.com")

    # Monitor specific div
    content_watcher = FilteredURLWatcher(css_selector="div.content")
    changed, diff = content_watcher.check_url("https://news.ycombinator.com")

    print(f"Changed: {changed}")
    if diff:
        print(f"Diff: {diff}")
```

## Real-World Scenarios

### 7. Product Price Monitoring

Monitor product prices on e-commerce sites:

```python
#!/usr/bin/env python3
"""
Monitor product prices with SMS alerts
"""
import re
import requests
from bs4 import BeautifulSoup
from url_watcher import URLWatcher
from sms_notifier import create_notifier_from_env

class PriceWatcher(URLWatcher):
    def __init__(self, price_selector, **kwargs):
        super().__init__(**kwargs)
        self.price_selector = price_selector

    def _fetch_url_content(self, url):
        """Extract only price information"""
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.select_one(self.price_selector)

        if price_element:
            price_text = price_element.get_text().strip()
            # Extract numeric price
            price_match = re.search(r'[\d,]+\.?\d*', price_text)
            if price_match:
                return f"Price: ${price_match.group()}"

        return "Price not found"

def monitor_product_price():
    # Setup SMS notifications
    sms_notifier = create_notifier_from_env()

    # Create price watcher (example CSS selector - adjust for actual site)
    watcher = PriceWatcher(
        price_selector=".price-current",
        sms_notifier=sms_notifier
    )

    product_url = "https://example-store.com/product/123"

    try:
        changed, diff = watcher.check_url(product_url)
        if changed:
            print(f"💰 Price changed for {product_url}")
            print(diff)
        else:
            print("💲 No price changes detected")
    except Exception as e:
        print(f"Error monitoring price: {e}")

if __name__ == "__main__":
    monitor_product_price()
```

### 8. News Feed Monitoring

Monitor news websites for new articles:

```python
#!/usr/bin/env python3
"""
Monitor news feeds for new articles
"""
import feedparser
from url_watcher import URLWatcher

class NewsFeedWatcher(URLWatcher):
    def _fetch_url_content(self, url):
        """Parse RSS/Atom feed and return formatted content"""
        feed = feedparser.parse(url)

        if feed.bozo:
            raise Exception(f"Invalid feed: {feed.bozo_exception}")

        content_lines = [f"Feed: {feed.feed.get('title', 'Unknown')}"]

        # Get latest 10 articles
        for entry in feed.entries[:10]:
            title = entry.get('title', 'No title')
            link = entry.get('link', '')
            published = entry.get('published', 'Unknown date')

            content_lines.append(f"- {title} ({published})")
            if link:
                content_lines.append(f"  {link}")

        return '\n'.join(content_lines)

def monitor_news():
    feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://rss.cnn.com/rss/edition.rss",
        "https://feeds.npr.org/1001/rss.xml"
    ]

    watcher = NewsFeedWatcher()

    for feed_url in feeds:
        try:
            changed, diff = watcher.check_url(feed_url)
            if changed:
                print(f"📰 New articles in {feed_url}")
                print(diff)
                print("-" * 50)
        except Exception as e:
            print(f"Error checking {feed_url}: {e}")

if __name__ == "__main__":
    monitor_news()
```

### 9. API Monitoring

Monitor REST API responses:

```python
#!/usr/bin/env python3
"""
Monitor API endpoints for changes
"""
import json
from url_watcher import URLWatcher

class APIWatcher(URLWatcher):
    def _fetch_url_content(self, url):
        """Format JSON responses for better diff viewing"""
        import requests

        response = requests.get(url, timeout=10)
        response.raise_for_status()

        try:
            # Pretty-print JSON for better diffs
            json_data = response.json()
            return json.dumps(json_data, indent=2, sort_keys=True)
        except json.JSONDecodeError:
            # Return raw content if not JSON
            return response.text

def monitor_api_endpoints():
    api_endpoints = [
        "https://api.github.com/zen",
        "https://httpbin.org/uuid",
        "https://api.coindesk.com/v1/bpi/currentprice.json"
    ]

    watcher = APIWatcher()

    for endpoint in api_endpoints:
        try:
            changed, diff = watcher.check_url(endpoint)
            if changed:
                print(f"🔄 API changed: {endpoint}")
                print(diff)
                print("=" * 60)
            else:
                print(f"✅ No changes: {endpoint}")
        except Exception as e:
            print(f"❌ Error: {endpoint} - {e}")

if __name__ == "__main__":
    monitor_api_endpoints()
```

## Integration Examples

### 10. Slack Integration

Send notifications to Slack when changes are detected:

```python
#!/usr/bin/env python3
"""
Send URL change notifications to Slack
"""
import requests
import json
from url_watcher import URLWatcher

class SlackNotifier:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_notification(self, url, message):
        """Send change notification to Slack"""
        payload = {
            "text": f"🔔 URL Change Detected",
            "attachments": [
                {
                    "color": "warning",
                    "fields": [
                        {
                            "title": "URL",
                            "value": url,
                            "short": False
                        },
                        {
                            "title": "Changes",
                            "value": f"```{message[:500]}```" if message else "Content changed",
                            "short": False
                        }
                    ]
                }
            ]
        }

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Slack notification failed: {e}")
            return False

class SlackURLWatcher(URLWatcher):
    def __init__(self, slack_notifier, **kwargs):
        super().__init__(**kwargs)
        self.slack_notifier = slack_notifier

    def check_url(self, url):
        changed, diff = super().check_url(url)
        if changed and self.slack_notifier:
            self.slack_notifier.send_notification(url, diff)
        return changed, diff

# Usage
if __name__ == "__main__":
    # Replace with your Slack webhook URL
    SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    slack_notifier = SlackNotifier(SLACK_WEBHOOK)
    watcher = SlackURLWatcher(slack_notifier=slack_notifier)

    # Monitor with Slack notifications
    watcher.watch_continuously("https://httpbin.org/uuid")
```

### 11. Database Logging

Log all URL changes to a database:

```python
#!/usr/bin/env python3
"""
Log URL changes to SQLite database
"""
import sqlite3
import json
from datetime import datetime
from url_watcher import URLWatcher

class DatabaseLogger:
    def __init__(self, db_path="url_changes.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS url_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                changed_at TIMESTAMP NOT NULL,
                diff_content TEXT,
                content_hash TEXT
            )
        """)

        conn.commit()
        conn.close()

    def log_change(self, url, diff_content, content_hash):
        """Log a URL change to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO url_changes (url, changed_at, diff_content, content_hash)
            VALUES (?, ?, ?, ?)
        """, (url, datetime.now(), diff_content, content_hash))

        conn.commit()
        conn.close()

    def get_changes(self, url=None, limit=10):
        """Get recent changes from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if url:
            cursor.execute("""
                SELECT * FROM url_changes
                WHERE url = ?
                ORDER BY changed_at DESC
                LIMIT ?
            """, (url, limit))
        else:
            cursor.execute("""
                SELECT * FROM url_changes
                ORDER BY changed_at DESC
                LIMIT ?
            """, (limit,))

        results = cursor.fetchall()
        conn.close()
        return results

class DatabaseURLWatcher(URLWatcher):
    def __init__(self, db_logger, **kwargs):
        super().__init__(**kwargs)
        self.db_logger = db_logger

    def check_url(self, url):
        changed, diff = super().check_url(url)
        if changed and self.db_logger:
            # Get current content hash
            content_hash = self.cache.get(url, {}).get('hash', '')
            self.db_logger.log_change(url, diff, content_hash)
        return changed, diff

# Usage
if __name__ == "__main__":
    # Setup database logging
    db_logger = DatabaseLogger()
    watcher = DatabaseURLWatcher(db_logger=db_logger)

    # Monitor and log changes
    watcher.watch_continuously("https://httpbin.org/uuid")

    # Query recent changes
    # recent_changes = db_logger.get_changes(limit=5)
    # for change in recent_changes:
    #     print(f"URL: {change[1]}, Changed: {change[2]}")
```

### 12. Webhook Integration

Send HTTP webhooks when changes are detected:

```python
#!/usr/bin/env python3
"""
Send webhook notifications for URL changes
"""
import requests
import json
from datetime import datetime
from url_watcher import URLWatcher

class WebhookNotifier:
    def __init__(self, webhook_url, secret=None):
        self.webhook_url = webhook_url
        self.secret = secret

    def send_webhook(self, url, diff_content):
        """Send webhook notification"""
        payload = {
            "event": "url_changed",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "url": url,
                "changed": True,
                "diff": diff_content,
                "diff_length": len(diff_content) if diff_content else 0
            }
        }

        headers = {'Content-Type': 'application/json'}

        # Add HMAC signature if secret provided
        if self.secret:
            import hmac
            import hashlib

            payload_bytes = json.dumps(payload).encode('utf-8')
            signature = hmac.new(
                self.secret.encode('utf-8'),
                payload_bytes,
                hashlib.sha256
            ).hexdigest()
            headers['X-Signature'] = f"sha256={signature}"

        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers=headers,
                timeout=10
            )

            print(f"Webhook sent: {response.status_code}")
            return response.status_code < 400
        except Exception as e:
            print(f"Webhook failed: {e}")
            return False

class WebhookURLWatcher(URLWatcher):
    def __init__(self, webhook_notifier, **kwargs):
        super().__init__(**kwargs)
        self.webhook_notifier = webhook_notifier

    def check_url(self, url):
        changed, diff = super().check_url(url)
        if changed and self.webhook_notifier:
            self.webhook_notifier.send_webhook(url, diff)
        return changed, diff

# Usage
if __name__ == "__main__":
    # Setup webhook notifications
    webhook_notifier = WebhookNotifier(
        webhook_url="https://your-server.com/webhook",
        secret="your-webhook-secret"
    )

    watcher = WebhookURLWatcher(webhook_notifier=webhook_notifier)
    watcher.watch_continuously("https://httpbin.org/uuid")
```

## Troubleshooting Common Issues

### 13. Handling Rate Limits

Deal with websites that have rate limiting:

```python
#!/usr/bin/env python3
"""
Handle rate limits with exponential backoff
"""
import time
import random
from url_watcher import URLWatcher
import requests

class RateLimitedWatcher(URLWatcher):
    def __init__(self, max_retries=3, base_delay=1, **kwargs):
        super().__init__(**kwargs)
        self.max_retries = max_retries
        self.base_delay = base_delay

    def _fetch_url_content(self, url):
        """Fetch with retry logic for rate limits"""
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, timeout=10, headers={
                    'User-Agent': 'URL-Watcher/1.0'
                })

                if response.status_code == 429:  # Rate limited
                    if attempt < self.max_retries:
                        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                        print(f"Rate limited, waiting {delay:.2f} seconds...")
                        time.sleep(delay)
                        continue

                response.raise_for_status()
                return response.text

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    delay = self.base_delay * (2 ** attempt)
                    print(f"Request failed (attempt {attempt + 1}), retrying in {delay}s...")
                    time.sleep(delay)
                    continue
                raise e

# Usage
watcher = RateLimitedWatcher(max_retries=3, base_delay=2)
watcher.watch_continuously("https://api.example.com/data")
```

### 14. Monitoring Password-Protected Sites

Monitor sites that require authentication:

```python
#!/usr/bin/env python3
"""
Monitor password-protected sites
"""
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from url_watcher import URLWatcher

class AuthenticatedWatcher(URLWatcher):
    def __init__(self, auth=None, cookies=None, headers=None, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        self.cookies = cookies
        self.headers = headers or {}

    def _fetch_url_content(self, url):
        """Fetch with authentication"""
        response = requests.get(
            url,
            auth=self.auth,
            cookies=self.cookies,
            headers=self.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.text

# Examples of different authentication methods

# Basic Auth
basic_auth_watcher = AuthenticatedWatcher(
    auth=HTTPBasicAuth('username', 'password')
)

# Digest Auth
digest_auth_watcher = AuthenticatedWatcher(
    auth=HTTPDigestAuth('username', 'password')
)

# Cookie-based auth
cookie_watcher = AuthenticatedWatcher(
    cookies={'session_id': 'your-session-cookie'}
)

# Token-based auth
token_watcher = AuthenticatedWatcher(
    headers={'Authorization': 'Bearer your-api-token'}
)

# Usage
try:
    changed, diff = basic_auth_watcher.check_url("https://httpbin.org/basic-auth/user/pass")
    print(f"Authentication successful, changed: {changed}")
except Exception as e:
    print(f"Authentication failed: {e}")
```

### 15. Large File Monitoring

Monitor only headers for large files:

```python
#!/usr/bin/env python3
"""
Monitor large files efficiently using HEAD requests
"""
import requests
from datetime import datetime
from url_watcher import URLWatcher

class HeaderOnlyWatcher(URLWatcher):
    def _fetch_url_content(self, url):
        """Use HEAD request to check only headers"""
        response = requests.head(url, timeout=10)
        response.raise_for_status()

        # Create content from relevant headers
        content_parts = []

        # Common headers that indicate file changes
        relevant_headers = [
            'Last-Modified',
            'ETag',
            'Content-Length',
            'Content-Type'
        ]

        for header in relevant_headers:
            if header in response.headers:
                content_parts.append(f"{header}: {response.headers[header]}")

        return '\n'.join(content_parts)

# Usage for monitoring large files
watcher = HeaderOnlyWatcher()

large_files = [
    "https://releases.ubuntu.com/20.04/ubuntu-20.04.6-desktop-amd64.iso",
    "https://download.mozilla.org/?product=firefox-latest&os=linux64"
]

for file_url in large_files:
    try:
        changed, diff = watcher.check_url(file_url)
        if changed:
            print(f"📦 File updated: {file_url}")
            print(diff)
        else:
            print(f"📦 No changes: {file_url}")
    except Exception as e:
        print(f"Error checking {file_url}: {e}")
```

### 16. Error Recovery and Resilience

Build resilient monitoring with comprehensive error handling:

```python
#!/usr/bin/env python3
"""
Resilient URL monitoring with comprehensive error handling
"""
import time
import logging
from datetime import datetime, timedelta
from url_watcher import URLWatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('url_monitor.log'),
        logging.StreamHandler()
    ]
)

class ResilientWatcher(URLWatcher):
    def __init__(self, max_consecutive_failures=5, failure_backoff=300, **kwargs):
        super().__init__(**kwargs)
        self.failure_counts = {}
        self.max_consecutive_failures = max_consecutive_failures
        self.failure_backoff = failure_backoff
        self.last_failure_time = {}

    def check_url_with_recovery(self, url):
        """Check URL with error recovery logic"""
        now = datetime.now()

        # Check if we're in backoff period
        if url in self.last_failure_time:
            time_since_failure = now - self.last_failure_time[url]
            if time_since_failure < timedelta(seconds=self.failure_backoff):
                logging.info(f"Skipping {url} - in backoff period")
                return False, None

        try:
            changed, diff = self.check_url(url)

            # Reset failure count on success
            if url in self.failure_counts:
                del self.failure_counts[url]
            if url in self.last_failure_time:
                del self.last_failure_time[url]

            logging.info(f"Successfully checked {url} - Changed: {changed}")
            return changed, diff

        except Exception as e:
            # Increment failure count
            self.failure_counts[url] = self.failure_counts.get(url, 0) + 1
            self.last_failure_time[url] = now

            failure_count = self.failure_counts[url]
            logging.error(f"Failed to check {url} ({failure_count} consecutive failures): {e}")

            # Stop checking URL if too many failures
            if failure_count >= self.max_consecutive_failures:
                logging.warning(f"Disabling {url} after {failure_count} consecutive failures")
                return None, None  # Signal to remove from monitoring

            return False, None

def resilient_monitoring():
    """Main monitoring loop with error recovery"""
    urls_to_monitor = [
        "https://httpbin.org/uuid",
        "https://httpbin.org/status/500",  # This will fail
        "https://invalid-domain-12345.com",  # This will fail
        "https://api.github.com/zen"
    ]

    watcher = ResilientWatcher(
        max_consecutive_failures=3,
        failure_backoff=600  # 10 minutes
    )

    active_urls = set(urls_to_monitor)

    while active_urls:
        logging.info(f"Checking {len(active_urls)} active URLs")

        urls_to_remove = []

        for url in list(active_urls):
            result = watcher.check_url_with_recovery(url)

            if result[0] is None:  # Signal to remove URL
                urls_to_remove.append(url)
                logging.warning(f"Removing {url} from monitoring")
            elif result[0]:  # Content changed
                logging.info(f"Content changed: {url}")
                if result[1]:
                    logging.info(f"Diff preview: {result[1][:200]}...")

        # Remove failed URLs
        for url in urls_to_remove:
            active_urls.remove(url)

        if not active_urls:
            logging.warning("No active URLs remaining")
            break

        logging.info("Sleeping for 60 seconds...")
        time.sleep(60)

if __name__ == "__main__":
    resilient_monitoring()
```

These examples demonstrate various ways to use the URL Watcher for different scenarios, from basic monitoring to advanced integrations with external services and robust error handling. Each example can be adapted to your specific needs and requirements.
