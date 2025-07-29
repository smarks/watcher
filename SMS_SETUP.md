# SMS Notifications Setup Guide

This guide explains how to set up SMS notifications for the URL Watcher using AWS SNS.

## Prerequisites

- AWS account with SNS access
- AWS CLI installed and configured
- Phone number that can receive SMS messages

## Step 1: Deploy AWS Infrastructure

1. Navigate to the `cloudformation/` directory
2. Run the deployment script with your phone number:

```bash
cd cloudformation
./deploy.sh -p "+1234567890"
```

Replace `+1234567890` with your actual phone number in E.164 format.

## Step 2: Configure Environment Variables

After the CloudFormation stack is deployed, you'll receive AWS credentials. Set these environment variables:

```bash
export AWS_ACCESS_KEY_ID="your_access_key_from_cloudformation_output"
export AWS_SECRET_ACCESS_KEY="your_secret_key_from_cloudformation_output"  
export AWS_REGION="us-east-1"
export SNS_TOPIC_ARN="your_topic_arn_from_cloudformation_output"
```

Or copy and modify the example configuration:

```bash
cp sms_config_example.sh sms_config.sh
# Edit sms_config.sh with your actual values
source sms_config.sh
```

## Step 3: Test SMS Notifications

Test your configuration:

```bash
python3 -c "
from sms_notifier import create_notifier_from_env
notifier = create_notifier_from_env()
result = notifier.test_notification()
print('Success!' if result['success'] else f'Error: {result[\"error\"]}')
"
```

## Step 4: Use URL Watcher with SMS

Now you can use the URL watcher with SMS notifications:

```bash
# Single check with SMS
python url_watcher.py http://example.com --sms

# Continuous monitoring with SMS
python url_watcher.py http://example.com --continuous --sms

# Both modes together
python url_watcher.py http://example.com --continuous --sms
```

## Testing the Feature

Run the SMS notification tests:

```bash
python test_sms_notifications.py
```

## CloudFormation Stack Details

The CloudFormation template creates:

- **SNS Topic**: For sending SMS notifications
- **SMS Subscription**: Links your phone number to the topic
- **IAM User**: With minimal permissions to publish to the topic
- **Access Keys**: For programmatic access

## Security Notes

- Store AWS credentials securely (consider using AWS IAM roles in production)
- The IAM user has minimal permissions (only SNS publish to the specific topic)
- Never commit AWS credentials to version control

## Troubleshooting

### SMS Not Received
- Verify phone number format (must be E.164: +1234567890)
- Check AWS SNS service limits
- Ensure your phone can receive SMS from AWS

### Authentication Errors
- Verify AWS credentials are correct
- Check IAM permissions
- Ensure region matches your SNS topic

### Topic Not Found
- Verify SNS_TOPIC_ARN is correct
- Check CloudFormation stack deployed successfully

## Cost Considerations

- SNS SMS pricing varies by country (usually $0.00645 per SMS in US)
- No charges for the SNS topic itself
- Minimal CloudFormation charges

## Cleanup

To remove AWS resources:

```bash
aws cloudformation delete-stack --stack-name url-watcher-sms
```