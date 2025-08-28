#!/usr/bin/env python3
"""
Check SMS usage and cost
"""
import boto3
from datetime import datetime, timedelta

def check_sms_cost():
    """Check SMS usage through CloudWatch metrics"""
    
    cloudwatch = boto3.client(
        'cloudwatch',
        aws_access_key_id="AKIAVVIGI22T5ZTXH3XS",
        aws_secret_access_key="***REMOVED***",
        region_name="us-east-1"
    )
    
    # Get SNS SMS metrics for the last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)
    
    try:
        print("Checking SMS message count in last 24 hours...")
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/SNS',
            MetricName='NumberOfMessagesSent',
            Dimensions=[
                {
                    'Name': 'TopicName',
                    'Value': 'url-watcher-notifications'
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,  # 1 hour intervals
            Statistics=['Sum']
        )
        
        total_messages = sum(point['Sum'] for point in response['Datapoints'])
        estimated_cost = total_messages * 0.00645  # $0.00645 per SMS in US
        
        print(f"📊 Total messages sent in last 24h: {total_messages}")
        print(f"💰 Estimated SMS cost: ${estimated_cost:.4f}")
        print(f"🚫 Monthly limit: $1.00")
        
        if estimated_cost >= 1.0:
            print("❌ You've likely hit your $1 monthly SMS spending limit!")
            print("💡 This is why you're not receiving SMS messages.")
        else:
            print("✅ You're under the spending limit.")
            
    except Exception as e:
        print(f"❌ Error checking metrics: {e}")
        print("This might be due to insufficient CloudWatch permissions.")

def suggest_solutions():
    """Suggest solutions for SMS delivery issues"""
    print("\n🔧 SOLUTIONS:")
    print("1. **Increase SMS Spending Limit:**")
    print("   - Go to AWS SNS Console → Mobile → Text messaging (SMS)")
    print("   - Request a spending limit increase")
    print("   - Or use AWS Support to request higher limit")
    print()
    print("2. **Check your phone:**")
    print("   - SMS might be in spam/blocked messages")
    print("   - Check if you've blocked unknown numbers")
    print("   - Try with a different phone number")
    print()
    print("3. **Alternative notification methods:**")
    print("   - Use email notifications instead")
    print("   - Use Slack/Discord webhooks")
    print("   - Use desktop notifications")
    print()
    print("4. **Test with a different region:**")
    print("   - Some regions have different SMS costs/limits")

if __name__ == "__main__":
    check_sms_cost()
    suggest_solutions()