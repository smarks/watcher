# URL Watcher 📡

> **A powerful, beginner-friendly URL monitoring tool that watches websites for changes and alerts you instantly**

[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/smarks/watcher)
[![Tests](https://img.shields.io/badge/tests-passing-green)](https://github.com/smarks/watcher/actions)
[![Python](https://img.shields.io/badge/python-3.9+-blue)](https://python.org)
[![Twilio](https://img.shields.io/badge/twilio-sms-red)](https://twilio.com/sms) [![AWS](https://img.shields.io/badge/aws-sns-orange)](https://aws.amazon.com/sns/)

**Perfect for beginners!** Monitor website changes, get SMS alerts, and learn Python automation. Written mostly by Claude AI under the careful direction of Spencer.

---

## 🎯 What Does This Do?

URL Watcher is like having a personal assistant that:
- 👀 **Watches websites** for any content changes  
- 📱 **Sends you SMS alerts** when something changes
- 🔍 **Shows you exactly** what changed with before/after comparisons
- ⏰ **Works 24/7** checking sites automatically
- 🆓 **Costs almost nothing** to run (Twilio SMS: ~$0.0075 per message, AWS SMS: ~$0.006 per message)

## 🚀 5-Minute Quick Start

### Step 1: Get the Code
```bash
git clone https://github.com/smarks/watcher.git
cd watcher
```

### Step 2: Install Requirements
```bash
pip install -r requirements.txt
```

### Step 3: Try It Out!
```bash
# Watch a website that changes frequently (UUID generator)
python url_watcher.py https://httpbin.org/uuid
```

**First run output:**
```
❌ No changes detected
First time checking this URL - no previous content to compare
```

**Run it again:**
```
✅ Content has CHANGED!

Difference:
--- https://httpbin.org/uuid (previous)  
+++ https://httpbin.org/uuid (current)
@@ -1,4 +1,4 @@
 {
   "args": {},
   "headers": { ... },
-  "uuid": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
+  "uuid": "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
 }
```

🎉 **Congratulations!** You just detected your first website change!

---

## 📋 Table of Contents

- [🎯 What Does This Do?](#-what-does-this-do)
- [🚀 5-Minute Quick Start](#-5-minute-quick-start)
- [📖 Complete Installation Guide](#-complete-installation-guide)
- [🎓 Beginner Tutorial](#-beginner-tutorial)
- [📱 SMS Notifications Setup](#-sms-notifications-setup)
- [💡 Real-World Examples](#-real-world-examples)
- [⚙️ Advanced Configuration](#️-advanced-configuration)
- [🧪 Testing & Coverage](#-testing--coverage)
- [🤖 CI/CD & GitHub Actions](#-cicd--github-actions)
- [🔧 API Reference](#-api-reference)
- [❓ Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📄 Additional Resources](#-additional-resources)

---

## 📖 Complete Installation Guide

### Prerequisites
- **Python 3.9+** ([Download here](https://python.org/downloads/))
- **pip** (comes with Python)
- **Git** ([Download here](https://git-scm.com/))
- **(Optional)** AWS account for SMS alerts

### Method 1: Simple Installation
```bash
# 1. Download the project
git clone https://github.com/smarks/watcher.git
cd watcher

# 2. Install dependencies
pip install -r requirements.txt

# 3. Test it works
python url_watcher.py --help
```

### Method 2: With Virtual Environment (Recommended)
```bash
# 1. Download the project  
git clone https://github.com/smarks/watcher.git
cd watcher

# 2. Create isolated Python environment
python -m venv venv

# 3. Activate the environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Test it works
python url_watcher.py --help
```

**Why use virtual environments?** They keep your project dependencies separate from your system Python, preventing conflicts.

### Verify Installation
```bash
python url_watcher.py https://httpbin.org/uuid
```

If you see output (either "No changes" or "Content changed"), you're ready to go! 🎉

---

## 🎓 Beginner Tutorial

### Lesson 1: Understanding URL Monitoring

**What is URL monitoring?**
- Imagine you want to know when your favorite website updates
- Instead of checking manually every hour, URL Watcher does it automatically
- It remembers what the website looked like and compares it to the current version

### Lesson 2: Your First Monitor

Let's monitor a website that changes every few seconds:

```bash
# Monitor a UUID generator (changes every time)
python url_watcher.py https://httpbin.org/uuid
```

Run this command twice - you'll see different UUIDs, proving change detection works!

### Lesson 3: Continuous Monitoring

Instead of running the command manually, let it run automatically:

```bash
# Check every 1-5 minutes automatically
python url_watcher.py https://httpbin.org/uuid --continuous
```

**Output:**
```
Starting continuous monitoring of: https://httpbin.org/uuid
Check interval: 60-300 seconds
Press Ctrl+C to stop

[2025-08-09 14:30:15] Checking URL...
✅ Content has CHANGED!
[Content differences shown here]

Next check in 187 seconds...
```

**To stop:** Press `Ctrl+C`

### Lesson 4: Monitor a Real Website

Let's try something practical:

```bash
# Monitor a news website's main page
python url_watcher.py https://example.com --continuous
```

### Lesson 5: Local Testing

Want to see how it works? Set up a test:

**Terminal 1 - Start a local web server:**
```bash
python -m http.server 8080
```

**Terminal 2 - Monitor your local server:**
```bash
python url_watcher.py http://localhost:8080 --continuous
```

**Terminal 3 - Make changes to trigger detection:**
```bash
echo "<h1>Hello World</h1>" > index.html
echo "<h1>Hello Universe!</h1>" > index.html  # This will trigger a change!
```

You'll see the change detection in Terminal 2! 🎉

---

## 📱 SMS Notifications Setup

Get instant text message alerts when websites change! Choose between Twilio (recommended) or AWS SNS.

### Option A: Twilio Setup (Recommended - Easier)

1. **Create a Twilio account:**
   - Go to [twilio.com](https://twilio.com) and sign up (free trial available)
   - Verify your phone number during signup

2. **Get your Twilio credentials:**
   - In Twilio Console, find your Account SID and Auth Token
   - Purchase a Twilio phone number (or use trial number)

3. **Set environment variables:**
   ```bash
   export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   export TWILIO_AUTH_TOKEN="your_auth_token"
   export TWILIO_FROM_PHONE="+15551234567"  # Your Twilio number
   export TWILIO_TO_PHONE="+19876543210"    # Your personal number
   ```

4. **Test configuration:**
   ```bash
   python twilio_notifier.py
   ```

5. **Use monitoring with SMS:**
   ```bash
   python url_watcher.py https://example.com --sms --continuous
   ```

### Option B: AWS SNS Setup (Legacy)

For users who prefer AWS or already have AWS infrastructure:

1. **Create SNS Topic in AWS Console:**
   - Go to AWS SNS Console
   - Click "Create Topic"  
   - Name: `url-watcher-notifications`
   - Type: Standard

2. **Subscribe your phone:**
   - Click your topic
   - Click "Create Subscription"
   - Protocol: SMS
   - Endpoint: Your phone number (+1234567890)
   - Confirm the subscription via SMS

3. **Create IAM User:**
   - Go to AWS IAM Console
   - Create user: `url-watcher-bot`
   - Attach policy: `AmazonSNSFullAccess` (or create custom minimal policy)
   - Create access keys

4. **Set environment variables:**
   ```bash
   export AWS_ACCESS_KEY_ID="your_access_key"
   export AWS_SECRET_ACCESS_KEY="your_secret_key"  
   export SNS_TOPIC_ARN="your_topic_arn"
   export AWS_REGION="us-east-1"
   ```

### SMS Message Example

When a website changes, you'll receive:
```
URL CHANGE DETECTED 🚨
Time: 2025-08-09 14:45:32
URL: https://example.com

Changes detected:
-<h1>Welcome to our site</h1>
+<h1>Welcome to our NEW site</h1>

Powered by URL Watcher
```

### Troubleshooting SMS

**Not receiving messages?**
- Verify phone number format: `+1234567890` (include country code)
- Check AWS SNS console for delivery status
- Ensure your phone can receive AWS messages (try AWS console test)
- Check AWS spending limits and SNS quotas

**Cost concerns?**
- SMS costs ~$0.006 per message in US
- CloudFormation/IAM are free
- Set AWS billing alerts for safety

---

## 💡 Real-World Examples

### Example 1: Monitor Product Prices
```bash
# Watch Amazon product page for price changes
python url_watcher.py "https://amazon.com/product/B08N5WRWNW" --continuous --sms
```

### Example 2: Job Postings
```bash  
# Monitor company careers page for new job listings
python url_watcher.py "https://company.com/careers" --continuous --sms
```

### Example 3: News Updates
```bash
# Get alerts when your local news site updates
python url_watcher.py "https://localnews.com" --continuous --sms
```

### Example 4: Stock/Crypto Prices
```bash
# Monitor a financial data page
python url_watcher.py "https://finance.yahoo.com/quote/AAPL" --continuous --sms
```

### Example 5: Government Announcements
```bash
# Watch for policy updates or announcements
python url_watcher.py "https://whitehouse.gov/news" --continuous --sms
```

### Example 6: Product Availability
```bash
# Monitor for "in stock" status changes
python url_watcher.py "https://store.com/limited-product" --continuous --sms
```

### Custom Intervals for Different Use Cases

**High-frequency monitoring (every 30 seconds to 2 minutes):**
```python
from url_watcher import URLWatcher

watcher = URLWatcher()
watcher.watch_continuously("https://fast-changing-site.com", min_interval=30, max_interval=120)
```

**Low-frequency monitoring (every 1-4 hours):**
```python
from url_watcher import URLWatcher

watcher = URLWatcher()  
watcher.watch_continuously("https://slow-changing-site.com", min_interval=3600, max_interval=14400)
```

---

## ⚙️ Advanced Configuration

### Environment Variables

Create a configuration file for easy setup:

**Create `config.sh`:**
```bash
#!/bin/bash
# URL Watcher Configuration

# AWS Settings (required for SMS)
export AWS_ACCESS_KEY_ID="your_aws_access_key"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key"
export AWS_REGION="us-east-1"
export SNS_TOPIC_ARN="arn:aws:sns:us-east-1:123456789012:your-topic"

# Optional: Custom cache location
export URL_CACHE_FILE="custom_cache.json"

echo "✅ URL Watcher configured!"
```

**Use it:**
```bash
source config.sh
python url_watcher.py https://example.com --sms --continuous
```

### Configuration Files

| File | Purpose | Auto-created? |
|------|---------|---------------|
| `url_cache.json` | Stores website snapshots | ✅ Yes |
| `.coverage_baseline.json` | Testing coverage tracking | ✅ Yes |
| `config.sh` | Your environment variables | ❌ Create manually |

### Programmatic Usage

**Basic monitoring in your own Python scripts:**
```python
from url_watcher import URLWatcher

# Create watcher
watcher = URLWatcher(storage_file="my_cache.json")

# Single check
changed, diff = watcher.check_url("https://example.com")
if changed:
    print("Website changed!")
    print(diff)
```

**With SMS notifications:**
```python
from url_watcher import URLWatcher
from sms_notifier import create_notifier_from_env

# Setup
sms = create_notifier_from_env()  # Uses environment variables
watcher = URLWatcher(sms_notifier=sms)

# Monitor
changed, diff = watcher.check_url("https://example.com")
if changed:
    print("Change detected and SMS sent!")
```

**Custom notification logic:**
```python
from url_watcher import URLWatcher
from datetime import datetime

def my_notification_handler(url, changes):
    # Send email, post to Slack, write to log, etc.
    print(f"ALERT: {url} changed!")
    print(changes)
    
    # Example: Write to log file
    with open("changes.log", "a") as f:
        f.write(f"{datetime.now()}: {url} changed\n{changes}\n\n")

watcher = URLWatcher()
changed, diff = watcher.check_url("https://example.com")
if changed:
    my_notification_handler("https://example.com", diff)
```

---

## 🧪 Testing & Coverage

### Quick Testing
```bash
# Run all tests
python -m pytest

# Run specific test
python -m pytest test_sms_notifications.py::TestSMSNotifier::test_send_notification_success

# Run with verbose output
python -m pytest -v
```

### Coverage Testing
```bash
# Run with coverage report
python -m pytest --cov=. --cov-report=html --cov-report=term-missing

# View detailed HTML report
open htmlcov/index.html  # Mac
# or
xdg-open htmlcov/index.html  # Linux
# or just open htmlcov/index.html in your browser
```

### Coverage Tracking & Regression Prevention

URL Watcher includes automatic coverage regression protection:

```bash
# Check coverage (fails if it drops)
python coverage_tracker.py

# Set new baseline
python coverage_tracker.py --reset-baseline

# Check without failing (just warn)  
python coverage_tracker.py --no-fail-on-decline

# Custom tolerance (allow 3% drop instead of default 2%)
python coverage_tracker.py --tolerance 3.0
```

**Current coverage: 100%** on core application files! 🎉

### Test Categories

| Test Type | File | Description |
|-----------|------|-------------|
| **Unit Tests** | `test_sms_notifications.py` | SMS functionality, AWS mocking |
| **Unit Tests** | `test_url_watcher.py` | Core monitoring logic |
| **Integration** | `integration_tests.py` | End-to-end scenarios |
| **Coverage** | `coverage_tracker.py` | Regression prevention |

---

## 🤖 CI/CD & GitHub Actions

URL Watcher includes professional-grade continuous integration:

### Automated Testing

Every code change triggers:
- ✅ **Multi-version testing** (Python 3.9, 3.10, 3.11, 3.12)
- ✅ **Coverage regression protection** (must maintain 100%)
- ✅ **Code formatting checks** (Black)
- ✅ **Security scanning** (Bandit)
- ✅ **Linting** (flake8)

### GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main/PR | Full CI pipeline |
| `test.yml` | Push/PR | Simple test runner |
| `coverage-guard.yml` | PR only | Coverage protection |

### Viewing Results

1. **Go to GitHub Actions tab** in the repository
2. **Click any workflow run** to see detailed results
3. **Check "Job Summary"** for coverage reports like:

```
📊 Coverage Report

| Branch | Coverage | Change |
|--------|----------|--------|
| main   | 100.0%   | baseline |
| feature| 99.0%    | -1.0%  |

📊 Coverage maintained (-1.0% change, within 2% tolerance)
✅ Within tolerance - small coverage changes are acceptable.
```

### Coverage Protection

PRs automatically get coverage analysis:
- ✅ **+2% or more**: "Coverage improved significantly"
- ✅ **0% to +2%**: "Coverage improved"  
- ✅ **-2% to 0%**: "Coverage maintained (within tolerance)"
- ❌ **Less than -2%**: "Significant regression detected" (fails CI)

---

## 🔧 API Reference

### URLWatcher Class

**Main monitoring class with simple, powerful methods.**

#### Constructor
```python
URLWatcher(storage_file="url_cache.json", sms_notifier=None)
```

**Parameters:**
- `storage_file` (str): Where to store website snapshots
- `sms_notifier` (SMSNotifier, optional): SMS handler for alerts

#### Methods

##### `check_url(url)` → `(bool, str)`
**Check a URL once and return results.**

```python
watcher = URLWatcher()
changed, diff = watcher.check_url("https://example.com")

if changed:
    print("Website changed!")
    print(f"Changes:\n{diff}")
else:
    print("No changes detected")
```

**Returns:**
- `changed` (bool): True if content changed
- `diff` (str): Text showing what changed (None if no changes)

##### `watch_continuously(url, min_interval=60, max_interval=300)`
**Monitor a URL forever with random intervals.**

```python
watcher = URLWatcher()

# Check every 1-5 minutes (default)
watcher.watch_continuously("https://example.com")

# Check every 30 seconds to 2 minutes
watcher.watch_continuously("https://example.com", 30, 120) 

# Check every hour to 4 hours
watcher.watch_continuously("https://example.com", 3600, 14400)
```

**Parameters:**
- `url` (str): Website to monitor
- `min_interval` (int): Minimum seconds between checks
- `max_interval` (int): Maximum seconds between checks

**Stops with:** Ctrl+C (KeyboardInterrupt)

### SMSNotifier Class

**Handles SMS alerts via AWS SNS.**

#### Constructor
```python
SMSNotifier(topic_arn=None, aws_access_key_id=None, 
           aws_secret_access_key=None, region_name='us-east-1')
```

#### Methods

##### `send_notification(url, message, subject=None)` → `bool`
**Send SMS about a website change.**

```python
from sms_notifier import SMSNotifier

sms = SMSNotifier(topic_arn="arn:aws:sns:us-east-1:123:topic")
success = sms.send_notification(
    url="https://example.com",
    message="Website content changed!",
    subject="URL Watcher Alert"
)

if success:
    print("SMS sent successfully!")
```

##### `test_notification()` → `dict`
**Test SMS configuration.**

```python
result = sms.test_notification()
print(result)
# {'success': True, 'message': 'Test SMS sent successfully', 'message_id': 'abc123'}
```

##### `is_configured()` → `bool`
**Check if SMS is properly set up.**

```python
if sms.is_configured():
    print("SMS ready!")
else:
    print("SMS not configured")
```

### Complete Example

```python
#!/usr/bin/env python3
"""
Complete example: Monitor website with SMS alerts
"""
from url_watcher import URLWatcher
from sms_notifier import create_notifier_from_env

def main():
    # Setup SMS (uses environment variables)
    sms = create_notifier_from_env()
    
    # Test SMS first
    if sms.is_configured():
        test_result = sms.test_notification()
        if test_result['success']:
            print("✅ SMS working!")
        else:
            print("❌ SMS test failed:", test_result)
            return
    else:
        print("⚠️  SMS not configured, running without notifications")
        sms = None
    
    # Create watcher with SMS
    watcher = URLWatcher(sms_notifier=sms)
    
    # Monitor website
    try:
        print("🔍 Starting monitoring...")
        watcher.watch_continuously("https://example.com", 60, 300)
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    main()
```

---

## ❓ Troubleshooting

### Common Issues & Solutions

#### 🔴 "ModuleNotFoundError" when running scripts
```bash
# Problem: Missing dependencies
# Solution:
pip install -r requirements.txt

# If that doesn't work, try:
python -m pip install requests boto3 pytest pytest-cov
```

#### 🔴 "AWS credentials not found"
```bash
# Problem: No AWS configuration
# Solution 1 - Environment variables:
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"

# Solution 2 - AWS CLI:
pip install awscli
aws configure
```

#### 🔴 "No changes detected" when you expect changes
- **Cause**: Website content might not actually be changing
- **Test**: Try `https://httpbin.org/uuid` (changes every time)
- **Debug**: Check if website uses JavaScript (we only see static HTML)

#### 🔴 SMS messages not received
```bash
# Check configuration
python -c "from sms_notifier import create_notifier_from_env; n=create_notifier_from_env(); print(n.test_notification())"

# Common fixes:
# 1. Phone number format: +1234567890 (include country code)
# 2. Check AWS SNS console for delivery failures
# 3. Verify phone can receive AWS messages
# 4. Check AWS spending limits
```

#### 🔴 "Permission denied" AWS errors
- **Cause**: IAM user needs SNS publish permissions
- **Fix**: Attach `AmazonSNSFullAccess` policy or create custom policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "sns:Publish",
            "Resource": "*"
        }
    ]
}
```

#### 🔴 CloudFormation deployment fails
- **Check AWS permissions**: Need CloudFormation, SNS, IAM access
- **Unique stack name**: Change name if stack already exists
- **Phone number format**: Must be E.164 format (+1234567890)
- **Service limits**: Check AWS SNS quotas in your region

### Getting Help

If you're still stuck:

1. **Check existing issues**: [GitHub Issues](https://github.com/smarks/watcher/issues)
2. **Create new issue** with:
   - Python version (`python --version`)
   - Operating system
   - Full error message
   - What you were trying to do
   - Minimal code to reproduce the problem

---

## 🤝 Contributing

We love contributions! Here's how to help make URL Watcher even better:

### Quick Contribution Guide

1. **Fork the repo** on GitHub
2. **Create a branch**: `git checkout -b feature/amazing-feature`
3. **Make changes and test them**
4. **Submit a pull request**

### Development Setup

```bash
# 1. Fork and clone your fork
git clone https://github.com/yourusername/watcher.git
cd watcher

# 2. Create development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install dependencies + dev tools
pip install -r requirements.txt

# 4. Run tests to make sure everything works
python -m pytest

# 5. Create your feature branch
git checkout -b feature/my-awesome-feature
```

### Testing Your Changes

```bash
# Run all tests
python -m pytest -v

# Check coverage (should stay at 100%)
python -m pytest --cov=. --cov-report=term-missing

# Test SMS functionality (with real AWS)
python -c "from sms_notifier import create_notifier_from_env; n=create_notifier_from_env(); print(n.test_notification())"

# Manual testing
python url_watcher.py https://httpbin.org/uuid
```

---

## 📄 Additional Resources

### Documentation Files

- **[SMS_SETUP.md](./SMS_SETUP.md)**: Detailed SMS configuration guide
- **[docs/EXAMPLES.md](./docs/EXAMPLES.md)**: Advanced usage examples
- **[docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md)**: Production deployment guide
- **[docs/API.md](./docs/API.md)**: Complete API documentation
- **[CLAUDE.md](./CLAUDE.md)**: Claude Code configuration

### Project Files

| File/Directory | Purpose |
|----------------|---------|
| `url_watcher.py` | 🎯 Main monitoring logic |
| `sms_notifier.py` | 📱 SMS notification system |
| `coverage_tracker.py` | 📊 Testing coverage management |
| `generate_coverage_badge.py` | 🏷️ README badge generation |
| `test_*.py` | 🧪 Test suites |
| `requirements.txt` | 📦 Python dependencies |
| `pyproject.toml` | ⚙️ Python project configuration |
| `cloudformation/` | ☁️ AWS infrastructure templates |
| `.github/workflows/` | 🤖 CI/CD automation |

### External Resources

- **[AWS SNS Documentation](https://docs.aws.amazon.com/sns/)**: SMS service docs
- **[Python Requests Library](https://docs.python-requests.org/)**: HTTP client docs  
- **[pytest Documentation](https://docs.pytest.org/)**: Testing framework docs
- **[GitHub Actions Guide](https://docs.github.com/en/actions)**: CI/CD automation

---

## 🏗 Architecture & Design

### Project Structure
```
watcher/
├── 🎯 Core Application
│   ├── url_watcher.py          # Main monitoring engine
│   ├── sms_notifier.py         # SMS notification system
│   └── requirements.txt        # Dependencies
├── 🧪 Testing & Quality
│   ├── test_sms_notifications.py    # SMS test suite
│   ├── test_url_watcher.py         # Core logic tests
│   ├── integration_tests.py        # End-to-end tests
│   ├── coverage_tracker.py         # Coverage regression protection
│   ├── generate_coverage_badge.py  # Badge generation
│   ├── pyproject.toml              # Python project config
│   └── pytest.ini                  # Test configuration
├── 🤖 CI/CD & Automation  
│   └── .github/workflows/
│       ├── ci.yml               # Main CI pipeline
│       ├── test.yml             # Simple test runner
│       └── coverage-guard.yml   # PR coverage protection
├── ☁️ Infrastructure
│   └── cloudformation/
│       ├── sns-setup.yaml       # AWS CloudFormation template
│       └── deploy.sh            # Deployment automation
├── 📚 Documentation
│   ├── README.md               # This comprehensive guide
│   ├── SMS_SETUP.md           # SMS setup instructions
│   ├── CLAUDE.md              # Claude Code configuration
│   └── docs/
│       ├── EXAMPLES.md         # Advanced examples
│       ├── DEPLOYMENT.md       # Production deployment
│       ├── API.md             # API documentation
│       └── TESTING.md         # Testing guide
└── 📄 Configuration
    ├── .gitignore             # Git ignore rules
    ├── index.html             # Test webpage
    └── sms_config_example.sh  # Environment setup template
```

### Design Principles

- **🔗 Separation of Concerns**: Monitoring logic separate from notifications
- **🛡️ Fail-Safe Design**: SMS failures don't break monitoring  
- **🧪 Test-Driven**: Comprehensive testing with mocking
- **⚙️ Configuration-Driven**: Environment-based setup
- **📦 Minimal Dependencies**: Only essential packages
- **🔄 Extensible**: Easy to add new notification channels

---

<div align="center">

## 🚀 Ready to Start Monitoring?

**URL Watcher** makes website monitoring simple, powerful, and reliable.

```bash
git clone https://github.com/smarks/watcher.git
cd watcher
pip install -r requirements.txt
python url_watcher.py https://httpbin.org/uuid
```

---

**Made with ❤️ by Spencer with assistance from Claude AI**

*A simple website watcher mostly written by Claude but under the careful direction of Spencer*

[⭐ Star on GitHub](https://github.com/smarks/watcher) • [📝 Report Issues](https://github.com/smarks/watcher/issues) • [🚀 Request Features](https://github.com/smarks/watcher/issues/new) • [💬 Discussions](https://github.com/smarks/watcher/discussions)

**Coverage:** ![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen) **Tests:** ![Tests](https://img.shields.io/badge/tests-passing-green) **Python:** ![Python](https://img.shields.io/badge/python-3.9+-blue)

</div>