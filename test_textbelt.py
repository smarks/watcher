#!/usr/bin/env python3
"""
Test script for TextBelt SMS integration
"""

from sms_notifier import SMSNotifier, create_notifier_from_env
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_textbelt_integration():
    """Test the TextBelt SMS integration"""
    
    try:
        print("Testing TextBelt SMS Integration...")
        print("=" * 50)
        
        # Create notifier from environment
        notifier = create_notifier_from_env()
        
        # Check configuration
        print(f"Phone number configured: {notifier.phone_number is not None}")
        print(f"API key configured: {notifier.api_key is not None}")
        print(f"Is configured: {notifier.is_configured()}")
        
        if not notifier.is_configured():
            print("\n❌ SMS notifications not properly configured")
            print("Please set SMS_PHONE_NUMBER and TEXTBELT_API_KEY in .env file")
            print("Example .env contents:")
            print("SMS_PHONE_NUMBER=+1234567890")
            print("TEXTBELT_API_KEY=your_api_key_here")
            return False
        
        print(f"\n📱 Configured to send SMS to: {notifier.phone_number}")
        
        # Test notification
        print("\nSending test notification...")
        result = notifier.test_notification()
        
        if result["success"]:
            print(f"✅ Test notification sent successfully!")
            print(f"TextId: {result.get('text_id')}")
        else:
            print(f"❌ Test notification failed: {result.get('error')}")
            return False
        
        # Test URL change notification
        print("\nTesting URL change notification...")
        test_url = "httpbin.org/uuid"  # Use domain only to avoid URL restrictions
        test_message = "Sample diff showing changes detected"
        
        success = notifier.send_notification(test_url, test_message)
        
        if success:
            print("✅ URL change notification sent successfully!")
        else:
            print("❌ URL change notification failed")
            return False
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error during testing: {e}")
        logging.error(f"Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_textbelt_integration()
    if not success:
        exit(1)