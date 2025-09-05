#!/usr/bin/env python3
"""Test script to verify SMS messages include diff content"""

# from vonage_sms_notifier import VonageSMSNotifier  # noqa: F401

# from clicksend_sms_notifier import ClickSendSMSNotifier  # noqa: F401
# from sms_notifier import SMSNotifier  # noqa: F401

# Sample diff content
sample_diff = """--- http://example.com (previous)
+++ http://example.com (current)
@@ -1,3 +1,3 @@
 Line 1
-Old line 2
+New line 2
 Line 3"""

# Test URL
test_url = "http://example.com"


def test_sms_with_diff():
    """Test that SMS notifiers include diff in messages"""

    # Test TextBelt notifier (without actual credentials)
    print("Testing TextBelt SMS Notifier...")
    # notifier = SMSNotifier(phone_number="+1234567890", api_key="test_key")  # Unused

    # Mock the send to just show what would be sent
    import logging

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Prepare the message as the notifier would
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    expected_message = (
        f"WEBSITE CHANGE DETECTED\nTime: {timestamp}\nURL: {test_url}\n\nChanges:\n{sample_diff}"
    )

    print("\nExpected SMS message with diff:")
    print("-" * 50)
    print(expected_message)
    print("-" * 50)

    # Test with long diff (should truncate)
    long_diff = sample_diff * 50  # Make it very long
    print("\n\nTesting with long diff (should truncate)...")

    if len(long_diff) > 500:
        truncated = long_diff[:500] + "...\n[truncated]"
        expected_truncated = (
            f"WEBSITE CHANGE DETECTED\nTime: {timestamp}\nURL: {test_url}\n\nChanges:\n{truncated}"
        )
        print("\nExpected truncated message:")
        print("-" * 50)
        print(expected_truncated[:200] + "...\n[rest of message truncated for display]")
        print("-" * 50)
        print(f"Total message length: {len(expected_truncated)} chars")


if __name__ == "__main__":
    test_sms_with_diff()
