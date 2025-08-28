#!/usr/bin/env python3
"""
Debug SMS sending with various approaches
"""
import boto3
import json
from datetime import datetime

def test_direct_sms():
    """Test direct SMS sending"""
    
    # Using the same credentials as before
    sns = boto3.client(
        'sns',
        aws_access_key_id="AKIAVVIGI22T5ZTXH3XS",
        aws_secret_access_key="***REMOVED***",
        region_name="us-east-1"
    )
    
    topic_arn = "arn:aws:sns:us-east-1:***REMOVED***:url-watcher-notifications"
    phone_number = "+1***REMOVED***"
    
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