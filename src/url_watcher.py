#!/usr/bin/env python3
"""
URL Content Monitor
Monitors URL content changes and reports differences
"""

import hashlib
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from difflib import unified_diff
from typing import Optional

import requests

from clicksend_sms_notifier import ClickSendSMSNotifier as SMSNotifier
from clicksend_sms_notifier import create_notifier_from_env


class URLWatcher:
    def __init__(self, storage_file="url_cache.json", sms_notifier: Optional[SMSNotifier] = None):
        self.storage_file = storage_file
        self.cache = self._load_cache()
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
            return (
                False,
                "First time checking this URL - no previous content to compare",
            )

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
                success = self.sms_notifier.send_notification(url, diff)
                if success:
                    logging.info(f"SMS notification sent successfully for URL: {url}")
                else:
                    logging.error(
                        f"SMS notification failed for URL: {url} - check logs for details"
                    )
            except Exception as e:
                logging.error(f"Unexpected error sending SMS notification for URL {url}: {e}")

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
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] " f"Checking URL...")

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

                # Wait for random interval with countdown
                wait_time = random.randint(min_interval, max_interval)
                print(f"Next check in {wait_time} seconds...")

                # Countdown timer - update every second
                for remaining in range(wait_time, 0, -1):
                    # Use \r to overwrite the same line
                    minutes, seconds = divmod(remaining, 60)
                    time_str = (
                        f"{minutes:02d}:{seconds:02d}" if minutes > 0 else f"{seconds} seconds"
                    )
                    print(f"\rNext check in: {time_str}  ", end="", flush=True)
                    time.sleep(1)

                # Clear the countdown line before the next check
                print("\r" + " " * 50 + "\r", end="")

        except KeyboardInterrupt:
            print("\n\nStopping continuous monitoring.")


def main():
    # Configure logging to show SMS notification failures
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if len(sys.argv) < 2:
        print("Usage: python url_watcher.py <URL> [--continuous] [--sms]")
        print("  Single check: python url_watcher.py <URL>")
        print("  Continuous:   python url_watcher.py <URL> --continuous")
        print("  With SMS:     python url_watcher.py <URL> --sms")
        print("  Both:         python url_watcher.py <URL> --continuous --sms")
        print("\nFor SMS notifications, set these environment variables:")
        print("  SMS_PHONE_NUMBER (e.g., '+1234567890'), CLICKSEND_USERNAME, CLICKSEND_API_KEY")
        sys.exit(1)

    url = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    # Check for invalid arguments and provide helpful error messages
    valid_args = {"--continuous", "--sms"}
    invalid_args = []
    for arg in args:
        if arg not in valid_args:
            # Check for common mistakes
            if arg.startswith("---") or arg.startswith("----"):
                invalid_args.append(f"'{arg}' (did you mean '--continuous' or '--sms'?)")
            elif arg in [
                "continuous",
                "-continuous",
                "---continuous",
                "----continuous",
            ]:
                invalid_args.append(f"'{arg}' (did you mean '--continuous'?)")
            elif arg in ["sms", "-sms", "---sms", "----sms"]:
                invalid_args.append(f"'{arg}' (did you mean '--sms'?)")
            else:
                invalid_args.append(f"'{arg}' (unknown argument)")

    if invalid_args:
        print(f"Error: Invalid argument(s): {', '.join(invalid_args)}")
        print("\nUsage: python url_watcher.py <URL> [--continuous] [--sms]")
        print("Valid arguments are: --continuous, --sms")
        sys.exit(1)

    continuous = "--continuous" in args
    enable_sms = "--sms" in args

    # Initialize SMS notifier if requested
    sms_notifier = None
    if enable_sms:
        sms_notifier = create_notifier_from_env()
        if not sms_notifier.is_configured():
            print("⚠️  SMS notifications requested but not properly configured")
            print(
                "Set SMS_PHONE_NUMBER, CLICKSEND_USERNAME, and CLICKSEND_API_KEY environment "
                "variables or add to .env file"
            )
        else:
            print("📱 SMS notifications enabled")

    watcher = URLWatcher(sms_notifier=sms_notifier)

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
