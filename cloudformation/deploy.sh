#!/bin/bash

# Deploy script for URL Watcher SMS CloudFormation stack

set -e

STACK_NAME="url-watcher-sms"
TEMPLATE_FILE="sns-setup.yaml"
PHONE_NUMBER=""

# Function to display usage
usage() {
    echo "Usage: $0 -p <phone_number> [-s <stack_name>]"
    echo "  -p: Phone number in E.164 format (e.g., +1234567890)"
    echo "  -s: Stack name (default: url-watcher-sms)"
    echo "  -h: Show this help message"
    exit 1
}

# Parse command line arguments
while getopts "p:s:h" opt; do
    case $opt in
        p)
            PHONE_NUMBER="$OPTARG"
            ;;
        s)
            STACK_NAME="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

# Validate required parameters
if [[ -z "$PHONE_NUMBER" ]]; then
    echo "Error: Phone number is required"
    usage
fi

# Validate phone number format
if [[ ! "$PHONE_NUMBER" =~ ^\+[1-9][0-9]{1,14}$ ]]; then
    echo "Error: Phone number must be in E.164 format (e.g., +1234567890)"
    exit 1
fi

echo "Deploying CloudFormation stack: $STACK_NAME"
echo "Phone number: $PHONE_NUMBER"
echo "Template: $TEMPLATE_FILE"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if user is authenticated
if ! aws sts get-caller-identity &> /dev/null; then
    echo "Error: AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

# Deploy the stack
echo "Creating/updating CloudFormation stack..."
aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        PhoneNumber="$PHONE_NUMBER" \
    --capabilities CAPABILITY_IAM \
    --no-fail-on-empty-changeset

if [[ $? -eq 0 ]]; then
    echo "Stack deployment completed successfully!"
    
    # Get outputs
    echo ""
    echo "Stack outputs:"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
        --output table
    
    echo ""
    echo "IMPORTANT: Save the AccessKeyId and SecretAccessKey values securely."
    echo "You'll need them to configure the URL watcher application."
    
else
    echo "Stack deployment failed!"
    exit 1
fi