#!/bin/bash
# SMS Configuration for URL Watcher

export AWS_ACCESS_KEY_ID="AKIAVVIGI22T5ZTXH3XS"
export AWS_SECRET_ACCESS_KEY="***REMOVED***"
export AWS_REGION="us-east-1"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:***REMOVED***:url-watcher-notifications"

echo "✅ SMS environment variables set!"
echo "📱 Phone number: +1***REMOVED***"
echo "🔔 Topic: url-watcher-notifications"

# Test configuration
python -c "
from sms_notifier import create_notifier_from_env
notifier = create_notifier_from_env()
print(f'SMS ready: {notifier.is_configured()}')
"