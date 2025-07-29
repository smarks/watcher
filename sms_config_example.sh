#!/bin/bash

# Example configuration script for SMS notifications
# Copy this file and update with your actual values

# Export AWS credentials and SNS topic ARN
export AWS_ACCESS_KEY_ID="your_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_secret_key_here"
export AWS_REGION="us-east-1"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:url-watcher-notifications"

# Test the configuration
echo "Testing SMS notification configuration..."
python3 -c "
from sms_notifier import create_notifier_from_env
notifier = create_notifier_from_env()
if notifier.is_configured():
    result = notifier.test_notification()
    if result['success']:
        print('✅ SMS notifications configured successfully!')
        print(f'Message ID: {result[\"message_id\"]}')
    else:
        print('❌ SMS test failed:', result['error'])
else:
    print('❌ SMS notifications not properly configured')
"

# Example usage
echo ""
echo "Example usage:"
echo "  Single check with SMS: python url_watcher.py http://example.com --sms"
echo "  Continuous with SMS:   python url_watcher.py http://example.com --continuous --sms"