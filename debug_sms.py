#!/usr/bin/env python3
"""
Debug SMS sending with various approaches
"""
import boto3
import json
import os
from datetime import datetime

def test_direct_sms():
    """Test direct SMS sending"""
    
    # Using credentials from environment variables
    sns = boto3.client(
        'sns',
        aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
        region_name=os.environ.get('AWS_REGION', 'us-east-1')
    )
    
    topic_arn = os.environ.get('SNS_TOPIC_ARN')
    phone_number = os.environ.get('SMS_PHONE_NUMBER')
    
    if not topic_arn or not phone_number:
        print("❌ Please set SNS_TOPIC_ARN and SMS_PHONE_NUMBER environment variables")
        return
    
    print("Testing SMS sending approaches...")
    
    # Test 1: Simple message to topic
    try:
        print("\n1. Sending simple message to topic...")
        response = sns.publish(
            TopicArn=topic_arn,
            Message="Hello from Python! Simple test message.",
            Subject="URL Watcher Test"
        )
        print(f"✅ Success - Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 2: Direct SMS to phone number
    try:
        print("\n2. Sending direct SMS to phone number...")
        response = sns.publish(
            PhoneNumber=phone_number,
            Message="Direct SMS test - bypassing topic"
        )
        print(f"✅ Success - Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Check account SMS attributes
    try:
        print("\n3. Checking SMS account settings...")
        attrs = sns.get_sms_attributes()
        print("SMS Attributes:")
        for key, value in attrs['attributes'].items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to get SMS attributes: {e}")
    
    # Test 4: Check topic attributes
    try:
        print("\n4. Checking topic attributes...")
        attrs = sns.get_topic_attributes(TopicArn=topic_arn)
        print("Topic Attributes:")
        for key, value in attrs['Attributes'].items():
            print(f"  {key}: {value}")
    except Exception as e:
        print(f"❌ Failed to get topic attributes: {e}")

if __name__ == "__main__":
    test_direct_sms()