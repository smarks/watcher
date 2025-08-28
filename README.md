# URL Watcher

A simple Python tool that monitors websites for content changes and sends SMS notifications via TextBelt.

## Features

- Monitor any URL for content changes
- SMS notifications when changes are detected
- Continuous monitoring with randomized intervals
- Secure credential storage via .env files
- Comprehensive test coverage

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up SMS notifications (optional):**
   Create a `.env` file:
   ```
   SMS_PHONE_NUMBER=+1234567890
   TEXTBELT_API_KEY=your_textbelt_api_key
   ```

3. **Monitor a URL:**
   ```bash
   # Single check
   python url_watcher.py https://example.com
   
   # Continuous monitoring
   python url_watcher.py https://example.com --continuous
   
   # With SMS alerts
   python url_watcher.py https://example.com --sms
   ```

## Usage

```bash
python url_watcher.py <URL> [--continuous] [--sms]
```

- `--continuous`: Monitor continuously with random intervals
- `--sms`: Send SMS notifications when changes are detected

## Requirements

- Python 3.9+
- TextBelt API account (for SMS notifications)

## Testing

```bash
pytest
```

## License

MIT