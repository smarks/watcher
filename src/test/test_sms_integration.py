#!/usr/bin/env python3
"""
Integration test for SMS notifications - actually sends SMS messages
Run this manually to verify your SMS configuration works
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from src.clicksend_sms_notifier import CLICKSEND_AVAILABLE, create_notifier_from_env
except ImportError:
    # Try direct import if running from project root
    from clicksend_sms_notifier import CLICKSEND_AVAILABLE, create_notifier_from_env


class TestSMSIntegration(unittest.TestCase):
    """Integration tests that actually send SMS messages"""

    def setUp(self):
        """Set up test - verify configuration"""
        self.notifier = create_notifier_from_env()

        # Check if we should run these tests
        self.skip_reason = None

        if not CLICKSEND_AVAILABLE:
            self.skip_reason = "ClickSend library not installed (pip install clicksend-client)"
        elif not self.notifier.is_configured():
            self.skip_reason = (
                "SMS not configured. Set environment variables:\n"
                "  SMS_PHONE_NUMBER (e.g., +1234567890)\n"
                "  CLICKSEND_USERNAME\n"
                "  CLICKSEND_API_KEY"
            )

    def test_verify_setup(self):
        """Test 1: Verify SMS configuration without sending"""
        if self.skip_reason:
            self.skipTest(self.skip_reason)

        print("\n" + "=" * 70)
        print("SMS CONFIGURATION CHECK")
        print("=" * 70)

        # Check configuration
        is_configured = self.notifier.is_configured()
        print(f"\n✓ Phone Number: {self.notifier.phone_number}")
        print(f"✓ Username: {self.notifier.username}")
        print(
            f"✓ API Key: {'*' * len(self.notifier.api_key) if self.notifier.api_key else 'Not set'}"
        )
        print(f"✓ Source: {self.notifier.source}")
        print(f"✓ Library Available: {CLICKSEND_AVAILABLE}")
        print(f"✓ Configuration Valid: {is_configured}")

        self.assertTrue(is_configured, "SMS should be properly configured")
        print("\n✅ SMS configuration is valid!\n")

    def test_send_test_sms(self):
        """Test 2: Actually send a test SMS message"""
        if self.skip_reason:
            self.skipTest(self.skip_reason)

        print("\n" + "=" * 70)
        print("SENDING TEST SMS")
        print("=" * 70)
        print(f"\nSending test SMS to: {self.notifier.phone_number}")
        print(f"Source: {self.notifier.source}")

        # Send test notification
        result = self.notifier.test_notification()

        # Display results
        print("\n" + "-" * 70)
        print("RESULT:")
        print("-" * 70)

        if result["success"]:
            print("✅ SUCCESS! Test SMS sent successfully")
            if "message_id" in result:
                print(f"   Message ID: {result['message_id']}")
            if "response" in result:
                print(f"   Response: {result['response']}")
        else:
            print("❌ FAILED to send test SMS")
            if "error" in result:
                print(f"   Error: {result['error']}")
            if "details" in result:
                print(f"   Details: {result['details']}")

        print("\n" + "=" * 70)

        self.assertTrue(
            result["success"],
            f"Test SMS should be sent successfully: {result.get('error', 'Unknown error')}",
        )
        print("\n✅ Check your phone for the test message!\n")

    def test_send_url_change_notification(self):
        """Test 3: Send a realistic URL change notification"""
        if self.skip_reason:
            self.skipTest(self.skip_reason)

        print("\n" + "=" * 70)
        print("SENDING URL CHANGE NOTIFICATION")
        print("=" * 70)

        # Simulate a URL change notification
        test_url = "https://example.com/test-page"
        test_diff = """--- Original content
+++ New content
@@ -1,3 +1,3 @@
 Line 1: Same content
-Line 2: Old content here
+Line 2: NEW content here!
 Line 3: Same content"""

        print(f"\nSimulating change detection for: {test_url}")
        print(f"Sending notification to: {self.notifier.phone_number}")

        # Send notification
        success = self.notifier.send_notification(test_url, test_diff)

        print("\n" + "-" * 70)
        print("RESULT:")
        print("-" * 70)

        if success:
            print("✅ SUCCESS! URL change notification sent")
        else:
            print("❌ FAILED to send URL change notification")

        print("\n" + "=" * 70)

        self.assertTrue(success, "URL change notification should be sent successfully")
        print("\n✅ Check your phone for the URL change notification!\n")


def run_interactive_test():
    """Run tests interactively with user prompts"""
    print("\n" + "=" * 70)
    print("SMS INTEGRATION TEST SUITE")
    print("=" * 70)
    print("\nThis will actually send SMS messages to your configured number.")
    print("Make sure you have set the following environment variables:")
    print("  - SMS_PHONE_NUMBER")
    print("  - CLICKSEND_USERNAME")
    print("  - CLICKSEND_API_KEY")
    print("\nOr create a .env file with these variables.")

    # Check configuration first
    notifier = create_notifier_from_env()

    if not CLICKSEND_AVAILABLE:
        print("\n❌ ERROR: ClickSend library not installed")
        print("Install with: pip install clicksend-client")
        return False

    if not notifier.is_configured():
        print("\n❌ ERROR: SMS not configured")
        print("Please set the required environment variables.")
        return False

    print("\n✓ Configuration detected:")
    print(f"  Phone: {notifier.phone_number}")
    print(f"  Username: {notifier.username}")
    print(f"  Source: {notifier.source}")

    response = input(
        "\n⚠️  Continue with SMS tests? " "This will send actual SMS messages. (yes/no): "
    )

    if response.lower() not in ["yes", "y"]:
        print("\nTest cancelled.")
        return False

    # Run the tests
    print("\n" + "=" * 70)
    print("RUNNING TESTS")
    print("=" * 70)

    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSMSIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Interactive mode with prompts
        success = run_interactive_test()
        sys.exit(0 if success else 1)
    else:
        # Standard unittest mode (will skip if not configured)
        print("\nRun with --interactive flag for guided testing")
        print("Example: python test_sms_integration.py --interactive\n")
        unittest.main(verbosity=2)
