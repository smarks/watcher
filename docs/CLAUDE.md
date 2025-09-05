# Claude Code Configuration

This file contains configuration and context for Claude Code to better assist with this project.

## Project Overview
URL Watcher - A Python application suite that monitors URLs for changes and sends SMS notifications. Includes both single-URL and multi-URL monitoring with resilience features.

## Applications

### Single URL Watcher (`url_watcher.py`)
Basic URL monitoring with SMS notifications
- Usage: `python url_watcher.py <URL> [--continuous] [--sms]`
- Examples:
  - `python url_watcher.py https://example.com --continuous --sms`
  - `python url_watcher.py https://example.com`

### Multi-URL Watcher (`multi_url_watcher.py`)
Advanced monitoring with resilience, retry logic, and multiple URL support
- Usage: `python multi_url_watcher.py <urls.json> [--sms]`
- Usage: `python multi_url_watcher.py <single-url> [--interval SECONDS] [--sms]`
- Examples:
  - `python multi_url_watcher.py urls.json --sms`
  - `python multi_url_watcher.py https://example.com --interval 60 --sms`

## Development Commands
- Test: `python -m pytest`
- Test Multi-URL: `python -m pytest test_multi_url_watcher.py -v`
- Lint: `flake8 . && black --check .`
- Format: `black .`
- Coverage: `python -m pytest --cov=. --cov-report=term-missing`

## Project Structure
- `url_watcher.py` - Basic single URL monitoring application
- `multi_url_watcher.py` - Advanced multi-URL monitoring with resilience
- `sms_notifier.py` - SMS notification via TextBelt API
- `vonage_sms_notifier.py` - SMS notification via Vonage API
- `clicksend_sms_notifier.py` - SMS notification via ClickSend API
- `coverage_tracker.py` - Coverage tracking and baseline management
- `test_*.py` - Unit test files
- `urls.json` - Configuration file for multi-URL monitoring
- `.env` - Environment variables (not in git)
- `sample.env` - Template for environment configuration
- `.flake8` - Flake8 linter configuration
- `pyproject.toml` - Black formatter and project configuration

## Configuration

### Environment Variables
SMS notifications require these environment variables (set in `.env` file):

**Common:**
- `SMS_PHONE_NUMBER` - Phone number for SMS (e.g., "+1234567890")

**Choose ONE SMS provider:**

**TextBelt:**
- `TEXTBELT_API_KEY` - TextBelt API key

**Vonage:**
- `VONAGE_API_KEY` - Vonage API key
- `VONAGE_API_SECRET` - Vonage API secret
- `VONAGE_FROM_NUMBER` - Sender ID (optional, default: "URLWatcher")

**ClickSend:**
- `CLICKSEND_USERNAME` - ClickSend username
- `CLICKSEND_API_KEY` - ClickSend API key
- `CLICKSEND_SOURCE` - Sender name (optional, default: "URLWatcher")

### Multi-URL Configuration (`urls.json`)
```json
[
  {"url": "https://example.com", "interval": 300},
  {"url": "https://api.github.com/repos/user/repo", "interval": 3600}
]
```

## Features

### Basic Features (Both Watchers)
- Content change detection using SHA256 hashing
- Diff generation showing exact changes
- SMS notifications with change details
- Comprehensive logging of all attempts
- Countdown timer for next check

### Advanced Features (Multi-URL Watcher Only)
- **Multiple URL Monitoring**: Monitor different URLs with individual intervals
- **Resilience**: 3 retry attempts with exponential backoff (5s, 10s, 20s)
- **Network Issue Handling**: Distinguish temporary failures from content changes
- **Unreachable Alerts**: SMS when sites go down and recover
- **Parallel Checking**: Check multiple URLs simultaneously when due
- **Statistics Tracking**: Per-URL check counts and last change timestamps
- **Recovery Notifications**: Alerts when sites come back online

## Important Notes
- Always run linting before committing: `flake8 . && black --check .`
- Use black for formatting: `black .`
- Max line length is configured to 100 characters
- Multi-URL watcher creates sample config if `urls.json` doesn't exist
- SMS messages include diff content (truncated to 500 chars for SMS limits)
- All SMS attempts are logged with clear success/failure indicators
