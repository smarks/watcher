#!/usr/bin/env python3
"""
URL Content Monitor
Monitors URL content changes and reports differences
"""

import sys
import requests
import hashlib
import json
import os
import time
import random
import logging
from datetime import datetime
from difflib import unified_diff
from typing import Optional

# Support both AWS SNS and Twilio SMS notifications
try:
    from sms_notifier import SMSNotifier, create_notifier_from_env as create_aws_notifier

    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    SMSNotifier = None
    create_aws_notifier = None

try:
    from twilio_notifier import TwilioNotifier, create_notifier_from_env as create_twilio_notifier

    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioNotifier = None
    create_twilio_notifier = None


class URLWatcher:
    def __init__(
        self,
        storage_file="url_cache.json",
        sms_notifier=None,  # Can be SMSNotifier (AWS) or TwilioNotifier
        notification_service="auto",  # "auto", "aws", "twilio", or "none"
    ):
        self.storage_file = storage_file
        self.cache = self._load_cache()
        self.notification_service = notification_service

        # Auto-detect notification service if not explicitly provided
        if sms_notifier is None and notification_service == "auto":
            self.sms_notifier = self._auto_detect_notification_service()
        else:
            self.sms_notifier = sms_notifier

    def _load_cache(self):
        """Load previous URL content cache from file"""
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _auto_detect_notification_service(self):
        """Auto-detect available notification service based on environment variables"""
        # Check for Twilio environment variables first (since we're prioritizing it)
        twilio_vars = [
            os.environ.get("TWILIO_ACCOUNT_SID"),
            os.environ.get("TWILIO_AUTH_TOKEN"),
            os.environ.get("TWILIO_FROM_PHONE"),
            os.environ.get("TWILIO_TO_PHONE"),
        ]

        if TWILIO_AVAILABLE and all(twilio_vars):
            print("📱 Auto-detected: Using Twilio SMS notifications")
            return create_twilio_notifier()

        # Fallback to AWS SNS if available
        aws_vars = [
            os.environ.get("SNS_TOPIC_ARN"),
            os.environ.get("AWS_ACCESS_KEY_ID"),
            os.environ.get("AWS_SECRET_ACCESS_KEY"),
        ]

        if AWS_AVAILABLE and all(aws_vars):
            print("☁️  Auto-detected: Using AWS SNS notifications")
            return create_aws_notifier()

        # No notification service detected
        print("📵 No SMS service configured (set TWILIO_* or AWS_* environment variables)")
        return None

    def _save_cache(self):
        """Save URL content cache to file"""
        with open(self.storage_file, "w") as f:
            json.dump(self.cache, f, indent=2)

    def _fetch_url_content(self, url):
        """Fetch content from URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {e}")

    def _get_content_hash(self, content):
        """Generate hash of content for quick comparison"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def check_url(self, url):
        """
        Check URL for changes
        Returns: (changed: bool, difference: str or None)
        """
        # Fetch current content
        current_content = self._fetch_url_content(url)
        current_hash = self._get_content_hash(current_content)

        # Check if we have previous content
        if url not in self.cache:
            # First time checking this URL
            self.cache[url] = {
                "content": current_content,
                "hash": current_hash,
                "last_checked": datetime.now().isoformat(),
            }
            self._save_cache()
            return False, "First time checking this URL - no previous content to compare"

        previous_content = self.cache[url]["content"]
        previous_hash = self.cache[url]["hash"]

        # Quick hash comparison
        if current_hash == previous_hash:
            # Update last checked time
            self.cache[url]["last_checked"] = datetime.now().isoformat()
            self._save_cache()
            return False, None

        # Content has changed - generate difference
        diff = self._generate_diff(previous_content, current_content, url)

        # Send SMS notification if configured
        if self.sms_notifier and self.sms_notifier.is_configured():
            try:
                self.sms_notifier.send_notification(url, diff)
                logging.info(f"SMS notification sent for URL: {url}")
            except Exception as e:
                logging.error(f"Failed to send SMS notification: {e}")

        # Update cache with new content
        self.cache[url] = {
            "content": current_content,
            "hash": current_hash,
            "last_checked": datetime.now().isoformat(),
        }
        self._save_cache()

        return True, diff

    def _generate_diff(self, old_content, new_content, url):
        """Generate human-readable difference between old and new content"""
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        diff_lines = list(
            unified_diff(
                old_lines,
                new_lines,
                fromfile=f"{url} (previous)",
                tofile=f"{url} (current)",
                lineterm="",
            )
        )

        if diff_lines:
            return "".join(diff_lines)
        else:
            return "Content changed but no line-by-line differences detected"

    def watch_continuously(self, url, min_interval=60, max_interval=300):
        """
        Continuously watch URL with random intervals between checks

        Args:
            url: URL to monitor
            min_interval: Minimum seconds between checks (default: 60 = 1 minute)
            max_interval: Maximum seconds between checks (default: 300 = 5 minutes)
        """
        print(f"Starting continuous monitoring of: {url}")
        print(f"Check interval: {min_interval}-{max_interval} seconds")
        print("Press Ctrl+C to stop")

        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking URL...")

                try:
                    changed, difference = self.check_url(url)

                    if changed:
                        print("✅ Content has CHANGED!")
                        print("\nDifference:")
                        print(difference)
                    else:
                        print("❌ No changes detected")
                        if difference:
                            print(difference)

                except Exception as e:
                    print(f"Error during check: {e}")

                # Wait for random interval
                wait_time = random.randint(min_interval, max_interval)
                print(f"Next check in {wait_time} seconds...")
                time.sleep(wait_time)

        except KeyboardInterrupt:
            print("\n\nStopping continuous monitoring.")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python url_watcher.py <URL> [--continuous] [--sms]")
        print("  Single check: python url_watcher.py <URL>")
        print("  Continuous:   python url_watcher.py <URL> --continuous")
        print("  With SMS:     python url_watcher.py <URL> --sms")
        print("  Both:         python url_watcher.py <URL> --continuous --sms")
        print("\nFor SMS notifications, set these environment variables:")
        print(
            "  Twilio (preferred): TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_PHONE, TWILIO_TO_PHONE"
        )
        print("  AWS SNS (legacy):   SNS_TOPIC_ARN, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        sys.exit(1)

    url = sys.argv[1]
    continuous = "--continuous" in sys.argv[2:]
    enable_sms = "--sms" in sys.argv[2:]

    # Initialize SMS notifier if requested (auto-detects Twilio vs AWS)
    watcher = URLWatcher(notification_service="auto" if enable_sms else "none")

    try:
        if continuous:
            watcher.watch_continuously(url)
        else:
            changed, difference = watcher.check_url(url)

            if changed:
                print("✅ Content has CHANGED!")
                print("\nDifference:")
                print(difference)
            else:
                print("❌ No changes detected")
                if difference:  # pragma: no cover
                    print(difference)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
