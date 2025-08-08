#!/usr/bin/env python3
"""
SMS Notification Module for URL Watcher
Sends SMS notifications via AWS SNS when URL changes are detected
"""

import os
import boto3
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError


class SMSNotifier:
    """Handles SMS notifications via AWS SNS"""

    def __init__(
        self,
        topic_arn: str = None,
        aws_access_key_id: str = None,
        aws_secret_access_key: str = None,
        region_name: str = "us-east-1",
    ):
        """
        Initialize SMS notifier

        Args:
            topic_arn: SNS topic ARN for sending SMS
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            region_name: AWS region name (default: us-east-1)
        """
        self.topic_arn = topic_arn or os.getenv("SNS_TOPIC_ARN")
        self.region_name = region_name

        # Initialize boto3 client
        try:
            if aws_access_key_id and aws_secret_access_key:
                self.sns_client = boto3.client(
                    "sns",
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                )
            else:
                # Use environment variables or IAM role
                self.sns_client = boto3.client("sns", region_name=region_name)

        except (NoCredentialsError, Exception) as e:
            logging.error(f"Failed to initialize AWS SNS client: {e}")
            self.sns_client = None

    def is_configured(self) -> bool:
        """Check if SMS notifications are properly configured"""
        return self.sns_client is not None and self.topic_arn is not None

    def send_notification(self, url: str, message: str, subject: str = None) -> bool:
        """
        Send SMS notification about URL change

        Args:
            url: The URL that changed
            message: Change description/diff
            subject: Optional subject line

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.is_configured():
            logging.warning("SMS notifications not configured - skipping")
            return False

        try:
            # Prepare message
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            sms_message = f"URL CHANGE DETECTED\n"
            sms_message += f"Time: {timestamp}\n"
            sms_message += f"URL: {url}\n\n"

            # Truncate message for SMS limits (160 chars for single SMS)
            if len(message) > 100:
                sms_message += f"Changes: {message[:100]}..."
            else:
                sms_message += f"Changes: {message}"

            # Send message
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=sms_message,
                Subject=subject or f"URL Change: {url[:50]}...",
            )

            message_id = response.get("MessageId")
            logging.info(f"SMS notification sent successfully. MessageId: {message_id}")
            return True

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            error_message = e.response["Error"]["Message"]
            logging.error(f"AWS SNS error ({error_code}): {error_message}")
            return False

        except Exception as e:
            logging.error(f"Unexpected error sending SMS: {e}")
            return False

    def test_notification(self) -> Dict[str, Any]:
        """
        Send a test notification to verify configuration

        Returns:
            dict: Test results with status and details
        """
        if not self.is_configured():
            return {
                "success": False,
                "error": "SMS notifications not configured",
                "details": {
                    "sns_client": self.sns_client is not None,
                    "topic_arn": self.topic_arn is not None,
                },
            }

        try:
            test_message = f"Test notification from URL Watcher at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            response = self.sns_client.publish(
                TopicArn=self.topic_arn, Message=test_message, Subject="URL Watcher Test"
            )

            return {
                "success": True,
                "message_id": response.get("MessageId"),
                "details": {"topic_arn": self.topic_arn, "region": self.region_name},
            }

        except ClientError as e:
            return {
                "success": False,
                "error": f"AWS SNS error: {e.response['Error']['Message']}",
                "error_code": e.response["Error"]["Code"],
            }

        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}


def create_notifier_from_env() -> SMSNotifier:
    """
    Create SMS notifier using environment variables

    Expected environment variables:
    - SNS_TOPIC_ARN: ARN of the SNS topic
    - AWS_ACCESS_KEY_ID: AWS access key ID
    - AWS_SECRET_ACCESS_KEY: AWS secret access key
    - AWS_REGION: AWS region (optional, defaults to us-east-1)
    """
    return SMSNotifier(
        topic_arn=os.getenv("SNS_TOPIC_ARN"),
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_REGION", "us-east-1"),
    )
