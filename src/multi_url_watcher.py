#!/usr/bin/env python3
"""
Multi-URL Content Monitor with Resilience
Monitors multiple URLs with different intervals and robust error handling
"""

import hashlib
import json
import logging
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from difflib import unified_diff
from typing import Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .clicksend_sms_notifier import ClickSendSMSNotifier as SMSNotifier
from .clicksend_sms_notifier import create_notifier_from_env


class ResilientURLWatcher:
    def __init__(
        self,
        storage_file="multi_url_cache.json",
        sms_notifier: Optional[SMSNotifier] = None,
        max_retries: int = 3,
        retry_delay: int = 5,
    ):
        self.storage_file = storage_file
        self.cache = self._load_cache()
        self.sms_notifier = sms_notifier
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.unreachable_urls: Dict[str, Dict] = {}  # Track unreachable URLs

        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

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

    def _fetch_url_content_with_retry(self, url: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Fetch content from URL with retry logic
        Returns: (success, content, error_message)
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                # If previously unreachable, send recovery notification
                if url in self.unreachable_urls:
                    self._send_recovery_notification(url)
                    del self.unreachable_urls[url]

                return True, response.text, None

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection failed: {str(e)}"
                logging.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {last_error}"
                )

            except requests.exceptions.Timeout as e:
                last_error = f"Request timed out: {str(e)}"
                logging.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {last_error}"
                )

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    last_error = f"Page not found (404): {str(e)}"
                    break  # Don't retry 404s
                else:
                    last_error = f"HTTP error: {str(e)}"
                logging.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {last_error}"
                )

            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"
                logging.warning(
                    f"Attempt {attempt + 1}/{self.max_retries} failed for {url}: {last_error}"
                )

            # Wait before retry (exponential backoff)
            if attempt < self.max_retries - 1:
                wait_time = self.retry_delay * (2**attempt)
                logging.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)

        # All retries failed
        error_message = last_error or "Unknown error"
        self._handle_unreachable_url(url, error_message)
        return False, None, error_message

    def _handle_unreachable_url(self, url: str, error: str):
        """Handle URL that became unreachable"""
        if url not in self.unreachable_urls:
            # First time becoming unreachable
            self.unreachable_urls[url] = {
                "first_failure": datetime.now(),
                "last_error": error,
                "notified": False,
            }

            # Send notification after confirming it's really down
            if not self.unreachable_urls[url]["notified"]:
                self._send_unreachable_notification(url, error)
                self.unreachable_urls[url]["notified"] = True
        else:
            # Update last error
            self.unreachable_urls[url]["last_error"] = error

    def _send_unreachable_notification(self, url: str, error: str):
        """Send notification that URL is unreachable"""
        message = (
            f"🔴 SITE UNREACHABLE\\n\\nURL: {url}\\nError: {error}\\n"
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        print(f"\\n🔴 ALERT: {url} is UNREACHABLE!")
        print(f"Error: {error}")

        if self.sms_notifier and self.sms_notifier.is_configured():
            try:
                self.sms_notifier.send_notification(url, message, subject="Site Down Alert")
                logging.info(f"Unreachable alert sent for {url}")
            except Exception as e:
                logging.error(f"Failed to send unreachable alert: {e}")

    def _send_recovery_notification(self, url: str):
        """Send notification that URL has recovered"""
        downtime_info = self.unreachable_urls.get(url)
        if downtime_info:
            downtime = datetime.now() - downtime_info["first_failure"]
            message = (
                f"🟢 SITE RECOVERED\\n\\nURL: {url}\\n"
                f"Downtime: {str(downtime).split('.')[0]}\\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            print(f"\\n🟢 RECOVERED: {url} is back online!")
            print(f"Downtime: {str(downtime).split('.')[0]}")

            if self.sms_notifier and self.sms_notifier.is_configured():
                try:
                    self.sms_notifier.send_notification(url, message, subject="Site Recovery Alert")
                    logging.info(f"Recovery alert sent for {url}")
                except Exception as e:
                    logging.error(f"Failed to send recovery alert: {e}")

    def _get_content_hash(self, content):
        """Generate hash of content for quick comparison"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def check_url(self, url: str) -> Tuple[bool, Optional[str], bool]:
        """
        Check URL for changes
        Returns: (changed: bool, difference: str or None, reachable: bool)
        """
        # Fetch current content with retry
        success, current_content, error = self._fetch_url_content_with_retry(url)

        if not success:
            return False, error, False

        current_hash = self._get_content_hash(current_content)

        # Check if we have previous content
        if url not in self.cache:
            # First time checking this URL
            self.cache[url] = {
                "content": current_content,
                "hash": current_hash,
                "last_checked": datetime.now().isoformat(),
                "check_count": 1,
            }
            self._save_cache()
            return False, "First time checking this URL - no previous content to compare", True

        previous_content = self.cache[url]["content"]
        previous_hash = self.cache[url]["hash"]

        # Quick hash comparison
        if current_hash == previous_hash:
            # Update last checked time and count
            self.cache[url]["last_checked"] = datetime.now().isoformat()
            self.cache[url]["check_count"] = self.cache[url].get("check_count", 0) + 1
            self._save_cache()
            logging.debug(f"Content Debug: No change detected for {url}")
            return False, None, True

        # Content has changed - generate difference
        logging.info(f"CONTENT CHANGED: Detected change for {url}")
        logging.debug(
            f"Content Debug: Old hash: {previous_hash[:10]}..., New hash: {current_hash[:10]}..."
        )
        diff = self._generate_diff(previous_content, current_content, url)

        # Send SMS notification if configured
        logging.debug(f"SMS Debug: sms_notifier exists: {self.sms_notifier is not None}")
        if self.sms_notifier:
            logging.debug(
                f"SMS Debug: sms_notifier configured: {self.sms_notifier.is_configured()}"
            )

        if self.sms_notifier and self.sms_notifier.is_configured():
            logging.info(f"ATTEMPTING SMS: Content changed for {url}, sending notification...")
            try:
                success = self.sms_notifier.send_notification(url, diff)
                if success:
                    logging.info(f"SMS notification sent successfully for URL: {url}")
                else:
                    logging.error(f"SMS notification failed for URL: {url}")
            except Exception as e:
                logging.error(f"Unexpected error sending SMS notification: {e}")
        else:
            logging.debug("SMS Debug: SMS notifier not configured or not available")

        # Update cache with new content
        self.cache[url] = {
            "content": current_content,
            "hash": current_hash,
            "last_checked": datetime.now().isoformat(),
            "last_changed": datetime.now().isoformat(),
            "check_count": self.cache[url].get("check_count", 0) + 1,
        }
        self._save_cache()

        return True, diff, True

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

    def watch_multiple_urls(self, urls_config: List[Dict], quiet: bool = False):
        """
        Watch multiple URLs with different intervals
        urls_config: List of dicts with 'url' and 'interval' (in seconds)
        quiet: If True, disable live countdown (useful for logging/redirected output)
        Example: [
            {'url': 'http://example.com', 'interval': 60},
            {'url': 'http://example.org', 'interval': 300}
        ]
        """
        print(f"Starting monitoring of {len(urls_config)} URLs")
        print("=" * 60)
        for config in urls_config:
            print(f"📍 {config['url']}")
            base = config["interval"]
            min_int = int(base * 0.8)
            max_int = int(base * 1.2)
            print(f"   Check interval: {base}s (randomized: {min_int}-{max_int}s)")
        print("=" * 60)
        print("Note: Intervals are randomized ±20% to avoid bot detection")
        print("Press Ctrl+C to stop\\n")

        # Track last check time for each URL
        last_checks = {
            config["url"]: datetime.now() - timedelta(seconds=config["interval"])
            for config in urls_config
        }

        try:
            while True:
                current_time = datetime.now()
                checks_to_run = []

                # Determine which URLs need checking
                for config in urls_config:
                    url = config["url"]
                    interval = config["interval"]
                    time_since_last = (current_time - last_checks[url]).total_seconds()

                    if time_since_last >= interval:
                        checks_to_run.append(config)

                # Run checks in parallel if multiple are due
                if checks_to_run:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = {}
                        for config in checks_to_run:
                            future = executor.submit(self._check_and_report, config["url"])
                            futures[future] = config

                        for future in as_completed(futures):
                            config = futures[future]
                            last_checks[config["url"]] = datetime.now()

                # Calculate next check time with randomization to avoid bot detection
                next_checks = []
                for config in urls_config:
                    url = config["url"]
                    base_interval = config["interval"]

                    # Add ±20% randomization to interval (e.g., 300s becomes 240-360s range)
                    min_interval = int(base_interval * 0.8)
                    max_interval = int(base_interval * 1.2)
                    randomized_interval = random.randint(min_interval, max_interval)

                    time_since_last = (datetime.now() - last_checks[url]).total_seconds()
                    time_until_next = max(0, randomized_interval - time_since_last)
                    next_checks.append((time_until_next, url, randomized_interval))

                next_checks.sort()
                if next_checks:
                    wait_time = max(1, int(next_checks[0][0]))
                    next_url = next_checks[0][1]
                    # next_interval = next_checks[0][2]  # Unused variable

                    if quiet:
                        # Quiet mode - just show when next check will happen and sleep
                        minutes, seconds = divmod(wait_time, 60)
                        time_str = f"{minutes:02d}:{seconds:02d}" if minutes > 0 else f"{seconds}s"
                        display_url = next_url[:50] + "..." if len(next_url) > 50 else next_url
                        print(f"Next check: {display_url} in {time_str}")
                        time.sleep(wait_time)
                    else:
                        # Interactive mode - show periodic countdown updates
                        display_url = next_url[:50] + "..." if len(next_url) > 50 else next_url
                        print(f"Next check: {display_url}")

                        # Show countdown at key intervals instead of every second
                        checkpoints = []
                        if wait_time > 60:
                            checkpoints = [wait_time, 60, 30, 10, 5, 1]
                        elif wait_time > 30:
                            checkpoints = [wait_time, 30, 10, 5, 1]
                        elif wait_time > 10:
                            checkpoints = [wait_time, 10, 5, 1]
                        else:
                            checkpoints = [wait_time, 1]

                        # Remove duplicates and sort
                        checkpoints = sorted(
                            list(set([c for c in checkpoints if c <= wait_time])), reverse=True
                        )

                        elapsed = 0
                        for i, checkpoint in enumerate(checkpoints):
                            sleep_time = checkpoint - (
                                checkpoints[i + 1] if i + 1 < len(checkpoints) else 0
                            )
                            if elapsed + sleep_time <= wait_time:
                                time.sleep(sleep_time)
                                elapsed += sleep_time
                                remaining = wait_time - elapsed
                                if remaining > 0:
                                    minutes, seconds = divmod(remaining, 60)
                                    time_str = (
                                        f"{minutes:02d}:{seconds:02d}"
                                        if minutes > 0
                                        else f"{seconds}s"
                                    )
                                    print(f"  ⏱️  {time_str} remaining...")

                        # Sleep any remaining time
                        if elapsed < wait_time:
                            time.sleep(wait_time - elapsed)

        except KeyboardInterrupt:
            print("\\n\\nStopping monitoring...")
            print("\\nStats:")
            print("=" * 60)
            for url in last_checks:
                if url in self.cache:
                    checks = self.cache[url].get("check_count", 0)
                    last_change = self.cache[url].get("last_changed", "Never")
                    if last_change != "Never":
                        last_change = last_change.split("T")[0]
                    print(f"📊 {url}")
                    print(f"   Total checks: {checks}")
                    print(f"   Last change: {last_change}")
            print("=" * 60)

    def _check_and_report(self, url: str):
        """Check a single URL and report results"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\\n[{timestamp}] Checking: {url}")

        try:
            changed, difference, reachable = self.check_url(url)

            if not reachable:
                print(f"   🔴 UNREACHABLE: {difference}")
            elif changed:
                print("   ✅ CHANGED!")
                # Only show first 200 chars of diff in multi-URL mode
                if difference and len(difference) > 200:
                    print(f"   Diff preview: {difference[:200]}...")
                else:
                    print(f"   Diff: {difference[:200] if difference else 'N/A'}")
            else:
                print("   ⚪ No changes")

        except Exception as e:
            print(f"   ❌ Error: {e}")


def load_urls_from_file(filename: str) -> List[Dict]:
    """Load URLs configuration from JSON file"""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file '{filename}' not found.")
        print("\\nCreating sample configuration file...")
        sample_config = [
            {"url": "https://example.com", "interval": 300},
            {"url": "https://example.org", "interval": 600},
        ]
        with open(filename, "w") as f:
            json.dump(sample_config, f, indent=2)
        print(f"Sample configuration saved to '{filename}'")
        print("Edit this file with your URLs and intervals, then run again.")
        sys.exit(0)
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        sys.exit(1)


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if len(sys.argv) < 2:
        print("Multi-URL Watcher with Resilience")
        print("=" * 40)
        print("\\nUsage:")
        print("  python multi_url_watcher.py <urls.json> [--sms] [--quiet]")
        print("  python multi_url_watcher.py <single-url> [--interval SECONDS] [--sms] [--quiet]")
        print("\\nExamples:")
        print("  python multi_url_watcher.py urls.json --sms")
        print("  python multi_url_watcher.py https://example.com --interval 60 --quiet")
        print("  python multi_url_watcher.py urls.json --sms --quiet")
        print("\\nOptions:")
        print("  --sms     Enable SMS notifications")
        print("  --quiet   Disable live countdown (better for logging/redirected output)")
        print("\\nFor SMS notifications, set environment variables:")
        print("  SMS_PHONE_NUMBER, CLICKSEND_USERNAME, CLICKSEND_API_KEY")
        sys.exit(1)

    # Parse arguments
    first_arg = sys.argv[1]
    args = sys.argv[2:]
    enable_sms = "--sms" in args
    quiet_mode = "--quiet" in args

    # Initialize SMS notifier if requested
    sms_notifier = None
    if enable_sms:
        sms_notifier = create_notifier_from_env()
        if not sms_notifier.is_configured():
            print("⚠️  SMS notifications requested but not properly configured")
        else:
            print("📱 SMS notifications enabled\\n")

    watcher = ResilientURLWatcher(sms_notifier=sms_notifier)

    # Check if first argument is a JSON file or URL
    if first_arg.endswith(".json"):
        # Multiple URLs from config file
        urls_config = load_urls_from_file(first_arg)
        watcher.watch_multiple_urls(urls_config, quiet=quiet_mode)
    else:
        # Single URL mode
        url = first_arg
        interval = 60  # default

        # Check for --interval flag
        if "--interval" in args:
            idx = args.index("--interval")
            if idx + 1 < len(args):
                try:
                    interval = int(args[idx + 1])
                except ValueError:
                    print(f"Error: Invalid interval value '{args[idx + 1]}'")
                    sys.exit(1)

        # Watch single URL
        urls_config = [{"url": url, "interval": interval}]
        watcher.watch_multiple_urls(urls_config, quiet=quiet_mode)


if __name__ == "__main__":
    main()
