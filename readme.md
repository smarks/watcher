# URL Watcher 📡

A powerful, lightweight URL monitoring tool that detects content changes and sends notifications. Built with Python and AWS integration.

[![Release](https://img.shields.io/github/v/release/smarks/watcher)](https://github.com/smarks/watcher/releases)
[![Tests](https://img.shields.io/badge/tests-passing-green)](./test_sms_notifications.py)
[![Python](https://img.shields.io/badge/python-3.7+-blue)](https://python.org)
[![AWS](https://img.shields.io/badge/aws-sns-orange)](https://aws.amazon.com/sns/)

> A simple website watcher mostly written by Claude but under the careful direction of Spencer

## ✨ Features

- **🔍 Content Monitoring**: Detects changes in web page content with diff visualization
- **⏰ Continuous Monitoring**: Configurable random intervals (1-5 minutes by default)
- **📱 SMS Notifications**: Optional AWS SNS integration for instant alerts
- **☁️ Infrastructure as Code**: CloudFormation templates for AWS setup
- **🧪 Comprehensive Testing**: Full test suite with mocking
- **🔧 Flexible Configuration**: Environment-based and command-line options

## 🚀 Quick Start

### Basic Usage

```bash
# Single URL check
python url_watcher.py https://example.com

# Continuous monitoring
python url_watcher.py https://example.com --continuous

# With SMS notifications
python url_watcher.py https://example.com --sms --continuous
```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/smarks/watcher.git
   cd watcher
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run your first check**
   ```bash
   python url_watcher.py https://httpbin.org/uuid
   ```

## 📋 Table of Contents

- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
- [SMS Notifications](#-sms-notifications)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

## 🛠 Installation & Setup

### Prerequisites

- Python 3.7 or higher
- pip package manager
- (Optional) AWS account for SMS notifications
- (Optional) AWS CLI for infrastructure deployment

### Step-by-Step Installation

1. **Clone and navigate**
   ```bash
   git clone https://github.com/smarks/watcher.git
   cd watcher
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation**
   ```bash
   python url_watcher.py --help
   ```

## 📖 Usage Guide

### Command Line Interface

```bash
python url_watcher.py <URL> [OPTIONS]
```

**Options:**
- `--continuous`: Enable continuous monitoring
- `--sms`: Enable SMS notifications (requires AWS setup)

### Basic Examples

#### Single Check
Monitor a URL once and exit:
```bash
python url_watcher.py https://example.com
```

Output:
```
❌ No changes detected
First time checking this URL - no previous content to compare
```

#### Continuous Monitoring
Monitor a URL continuously with random intervals:
```bash
python url_watcher.py https://example.com --continuous
```

Output:
```
Starting continuous monitoring of: https://example.com
Check interval: 60-300 seconds
Press Ctrl+C to stop

[2025-07-29 16:45:32] Checking URL...
❌ No changes detected
Next check in 187 seconds...
```

#### With Change Detection
When content changes are detected:
```
[2025-07-29 16:48:39] Checking URL...
✅ Content has CHANGED!

Difference:
--- https://example.com (previous)
+++ https://example.com (current)
@@ -1,3 +1,3 @@
 <html>
 <body>
-<h1>Hello World</h1>
+<h1>Hello Universe</h1>
 </body>
 </html>
```

### Local Testing Server

For testing purposes, you can run a local HTTP server:

```bash
# Start server on port 8080
python -m http.server 8080

# In another terminal, monitor it
python url_watcher.py http://localhost:8080 --continuous
```

Then modify `index.html` to see change detection in action.

## 📱 SMS Notifications

The URL Watcher can send SMS notifications via AWS SNS when changes are detected.

### Quick Setup

1. **Deploy AWS infrastructure**
   ```bash
   cd cloudformation
   ./deploy.sh -p "+1234567890"  # Your phone number
   ```

2. **Configure environment variables**
   ```bash
   export AWS_ACCESS_KEY_ID="your_key_from_cloudformation"
   export AWS_SECRET_ACCESS_KEY="your_secret_from_cloudformation"
   export AWS_REGION="us-east-1"
   export SNS_TOPIC_ARN="your_topic_arn_from_cloudformation"
   ```

3. **Test SMS configuration**
   ```bash
   python -c "from sms_notifier import create_notifier_from_env; print('✅ Configured!' if create_notifier_from_env().test_notification()['success'] else '❌ Error')"
   ```

4. **Use with SMS enabled**
   ```bash
   python url_watcher.py https://example.com --sms --continuous
   ```

### SMS Message Format

When a change is detected, you'll receive an SMS like:
```
URL CHANGE DETECTED
Time: 2025-07-29 16:45:32
URL: https://example.com

Changes: <html>
<body>
-<h1>Hello World</h1>
+<h1>Hello Universe</h1>
</body>
</html>
```

For detailed SMS setup, see [SMS_SETUP.md](./SMS_SETUP.md).

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required for SMS |
|----------|-------------|------------------|
| `SNS_TOPIC_ARN` | AWS SNS Topic ARN | ✅ |
| `AWS_ACCESS_KEY_ID` | AWS Access Key | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Key | ✅ |
| `AWS_REGION` | AWS Region | Optional (default: us-east-1) |

### Configuration Files

- **`url_cache.json`**: Stores previous URL content and metadata
- **`sms_config_example.sh`**: Template for environment variable setup
- **`CLAUDE.md`**: Project-specific Claude Code configuration

### Customizing Check Intervals

For continuous monitoring, you can customize intervals programmatically:

```python
from url_watcher import URLWatcher

watcher = URLWatcher()
# Custom intervals: 30 seconds to 2 minutes
watcher.watch_continuously("https://example.com", min_interval=30, max_interval=120)
```

## 📚 API Reference

### URLWatcher Class

The main class for URL monitoring functionality.

#### Constructor
```python
URLWatcher(storage_file="url_cache.json", sms_notifier=None)
```

**Parameters:**
- `storage_file` (str): Path to cache file for storing URL states
- `sms_notifier` (SMSNotifier, optional): SMS notification handler

#### Methods

##### `check_url(url)`
Performs a single check of the specified URL.

**Parameters:**
- `url` (str): The URL to monitor

**Returns:**
- `tuple`: `(changed: bool, difference: str or None)`

**Example:**
```python
watcher = URLWatcher()
changed, diff = watcher.check_url("https://example.com")
if changed:
    print("Content changed!")
    print(diff)
```

##### `watch_continuously(url, min_interval=60, max_interval=300)`
Continuously monitors a URL with random intervals.

**Parameters:**
- `url` (str): The URL to monitor
- `min_interval` (int): Minimum seconds between checks (default: 60)
- `max_interval` (int): Maximum seconds between checks (default: 300)

**Example:**
```python
watcher = URLWatcher()
# Check every 30-120 seconds
watcher.watch_continuously("https://example.com", 30, 120)
```

### SMSNotifier Class

Handles SMS notifications via AWS SNS.

#### Constructor
```python
SMSNotifier(topic_arn=None, aws_access_key_id=None, 
           aws_secret_access_key=None, region_name='us-east-1')
```

#### Methods

##### `send_notification(url, message, subject=None)`
Sends an SMS notification about a URL change.

**Parameters:**
- `url` (str): The URL that changed
- `message` (str): The change description/diff
- `subject` (str, optional): Message subject

**Returns:**
- `bool`: True if sent successfully, False otherwise

##### `test_notification()`
Sends a test SMS to verify configuration.

**Returns:**
- `dict`: Test results with success status and details

### Utility Functions

##### `create_notifier_from_env()`
Creates an SMSNotifier using environment variables.

**Returns:**
- `SMSNotifier`: Configured SMS notifier instance

## 🧪 Testing

The project includes comprehensive test suites for all functionality.

### Running Tests

```bash
# Run all SMS notification tests
python test_sms_notifications.py

# Run basic URL watcher tests
python test_watcher.py

# Run specific test
python -m unittest test_sms_notifications.TestSMSNotifier.test_send_notification_success
```

### Test Coverage

- **SMS Functionality**: 17 test cases covering AWS integration, error handling, and edge cases
- **URL Monitoring**: Integration tests with local server
- **Configuration**: Environment variable and credential testing
- **Error Handling**: Network failures, AWS errors, and malformed responses

### Testing with Local Server

For integration testing:

```bash
# Terminal 1: Start test server
python -m http.server 8080

# Terminal 2: Run tests
python test_watcher.py
```

### Mocking AWS Services

Tests use `unittest.mock` to simulate AWS SNS responses without making real API calls:

```python
@patch('boto3.client')
def test_sms_functionality(self, mock_boto_client):
    mock_client = Mock()
    mock_client.publish.return_value = {'MessageId': 'test-123'}
    mock_boto_client.return_value = mock_client
    # Test implementation...
```

## 🚀 Deployment

### Local Deployment

1. **Clone and setup**
   ```bash
   git clone https://github.com/smarks/watcher.git
   cd watcher
   pip install -r requirements.txt
   ```

2. **Run monitoring**
   ```bash
   python url_watcher.py https://your-website.com --continuous
   ```

### AWS Infrastructure Deployment

The project includes CloudFormation templates for automated AWS setup.

#### Prerequisites
- AWS CLI installed and configured
- AWS account with SNS and IAM permissions

#### Deployment Steps

1. **Deploy infrastructure**
   ```bash
   cd cloudformation
   ./deploy.sh -p "+1234567890"
   ```

2. **Configure environment**
   ```bash
   # Get outputs from CloudFormation
   aws cloudformation describe-stacks --stack-name url-watcher-sms --query 'Stacks[0].Outputs'
   
   # Set environment variables
   export AWS_ACCESS_KEY_ID="..."
   export AWS_SECRET_ACCESS_KEY="..."
   export SNS_TOPIC_ARN="..."
   ```

3. **Start monitoring with SMS**
   ```bash
   python url_watcher.py https://your-website.com --continuous --sms
   ```

#### Infrastructure Components

The CloudFormation template creates:

- **SNS Topic**: For SMS message delivery
- **SMS Subscription**: Links phone number to topic
- **IAM User**: With minimal SNS publish permissions
- **Access Keys**: For programmatic access

#### Cost Considerations

- SNS SMS: ~$0.00645 per message (US)
- CloudFormation: No additional charges
- IAM: No charges for users/policies

### Production Considerations

- **Security**: Use IAM roles instead of access keys when possible
- **Monitoring**: Set up CloudWatch alarms for failures
- **Scaling**: Consider rate limiting for high-frequency checks
- **Reliability**: Implement retry logic for network failures

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

1. **Fork and clone**
   ```bash
   git clone https://github.com/yourusername/watcher.git
   cd watcher
   ```

2. **Create development environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Contribution Guidelines

- **Code Style**: Follow PEP 8 Python style guidelines
- **Testing**: Add tests for new functionality
- **Documentation**: Update docs for user-facing changes
- **Commits**: Use descriptive commit messages

### Submitting Changes

1. **Run tests**
   ```bash
   python test_sms_notifications.py
   python test_watcher.py
   ```

2. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: description of your changes"
   ```

3. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Feature Requests

Open an issue on GitHub with:
- Clear description of the feature
- Use cases and benefits
- Potential implementation approach

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

### Getting Help

- **Documentation**: Check this README and [SMS_SETUP.md](./SMS_SETUP.md)
- **Issues**: Report bugs on [GitHub Issues](https://github.com/smarks/watcher/issues)
- **Discussions**: Ask questions in [GitHub Discussions](https://github.com/smarks/watcher/discussions)

### Common Issues

#### "Module not found" errors
```bash
pip install -r requirements.txt
```

#### AWS credentials errors
```bash
aws configure
# or
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
```

#### CloudFormation deployment fails
- Check AWS permissions (SNS, IAM, CloudFormation)
- Verify phone number format (+1234567890)
- Ensure unique stack name

### Troubleshooting

#### SMS not received
- Verify phone number format (E.164: +1234567890)
- Check AWS SNS service quotas
- Confirm phone can receive SMS from AWS

#### High memory usage
- Clear cache file: `rm url_cache.json`
- Reduce check frequency for large pages
- Monitor with `top` or `htop`

## 🏗 Architecture

### Project Structure

```
watcher/
├── url_watcher.py          # Main monitoring logic
├── sms_notifier.py         # SMS notification handler
├── test_sms_notifications.py # SMS test suite
├── test_watcher.py         # Basic tests
├── requirements.txt        # Python dependencies
├── README.md              # This documentation
├── SMS_SETUP.md           # SMS setup guide
├── CLAUDE.md              # Claude Code configuration
├── sms_config_example.sh  # Environment setup template
├── index.html             # Test web page
├── cloudformation/        # AWS infrastructure
│   ├── sns-setup.yaml     # CloudFormation template
│   └── deploy.sh          # Deployment script
└── .gitignore            # Git ignore rules
```

### Design Principles

- **Separation of Concerns**: Core monitoring separate from notifications
- **Fail-Safe**: SMS failures don't break monitoring
- **Testable**: Comprehensive mocking for external dependencies
- **Configurable**: Environment-based configuration
- **Minimal Dependencies**: Only essential packages

## 🔮 Roadmap

### Planned Features

- **Multiple Notification Channels**: Email, Slack, Discord
- **Web Dashboard**: Browser-based monitoring interface
- **Advanced Filtering**: CSS selectors, XPath expressions
- **Scheduling**: Cron-like scheduling options
- **Metrics**: Prometheus/Grafana integration
- **Database Storage**: PostgreSQL/MySQL support

### Version History

- **v0.1**: Initial release with basic monitoring and SMS notifications
- **v0.2**: (Planned) Web dashboard and multiple notification channels

---

<div align="center">

**URL Watcher** - Monitor the web, stay informed 📡

Made with ❤️ by Spencer with assistance from Claude

[⭐ Star on GitHub](https://github.com/smarks/watcher) | [📝 Report Issue](https://github.com/smarks/watcher/issues) | [🚀 Request Feature](https://github.com/smarks/watcher/issues/new)

</div>