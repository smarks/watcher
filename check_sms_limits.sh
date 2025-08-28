#!/bin/bash

echo "🔍 Checking your current SMS configuration..."

echo "
📋 TO INCREASE SMS SPENDING LIMIT:

1. 🌐 Open AWS Console:
   https://us-east-1.console.aws.amazon.com/sns/v3/home?region=us-east-1#/mobile/text-messaging

2. 📱 Navigate to SMS Settings:
   - Click 'Mobile' → 'Text messaging (SMS)'
   - Look for 'Account-level preferences'

3. 💰 Update Spending Limit:
   - Find 'Monthly spending quota for SMS messages'
   - Change from \$1.00 to \$10.00
   - Click 'Save changes'

4. ⚡ Test Immediately:
   - Go back to your terminal
   - Run: source set_sms_config.sh && python test_sms_now.py

📊 SMS COSTS:
- Each SMS: ~\$0.0065
- Current limit (\$1): ~154 messages/month  
- New limit (\$10): ~1,538 messages/month

🚨 If you can't increase the limit:
- You may need AWS Support to raise account limits
- Or we can switch to email notifications instead
"

# Check current SMS attributes
echo "Current SMS settings:"
aws sns get-sms-attributes 2>/dev/null || echo "❌ Cannot check SMS attributes (permission issue)"