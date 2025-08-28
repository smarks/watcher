#!/usr/bin/env python3
"""
Test SMS functionality with explicit configuration
"""
import os
from sms_notifier import SMSNotifier

# Set configuration directly
AWS_ACCESS_KEY_ID = "AKIAVVIGI22T5ZTXH3XS"
AWS_SECRET_ACCESS_KEY = "***REMOVED***"
AWS_REGION = "us-east-1"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:***REMOVED***:url-watcher-notifications"

def test_sms():
    print("Testing SMS with explicit configuration...")
    
    try:
        # Create notifier with explicit parameters
        notifier = SMSNotifier(
            topic_arn=SNS_TOPIC_ARN,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )
        
        print(f"✅ SNS client created: {notifier.sns_client is not None}")
        print(f"✅ Topic ARN set: {notifier.topic_arn is not None}")
        print(f"✅ Is configured: {notifier.is_configured()}")
        
        if notifier.is_configured():
            print("\n📱 Sending test SMS...")
            result = notifier.test_notification()
            
            if result['success']:
                print(f"🎉 SUCCESS! SMS sent with Message ID: {result['message_id']}")
                print("Check your phone for the test message!")
            else:
                print(f"❌ FAILED: {result['error']}")
                if 'error_code' in result:
                    print(f"AWS Error Code: {result['error_code']}")
        else:
            print("❌ SMS not properly configured")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sms()