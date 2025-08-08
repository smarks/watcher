# Watcher 

A simple website watcher mostly written by Claude but under the careful direction of Spencer

## Setup

**Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Usage

 - Single check: python url_watcher.py <URL>
 - Continuous:   python url_watcher.py <URL> --continuous
 - With SMS:     python url_watcher.py <URL> --sms
 - Both:         python url_watcher.py <URL> --continuous --sms

## Testing

**Run tests:**
```bash
pytest
```

**Run tests with coverage:**
```bash
pytest --cov=url_watcher --cov=sms_notifier --cov-report=html --cov-report=term-missing
```

View detailed coverage report: open `htmlcov/index.html` in browser

**Coverage tracking (prevents coverage regression):**
```bash
# Run coverage check with regression detection
python coverage_tracker.py

# Don't fail on coverage decline (just warn)
python coverage_tracker.py --no-fail-on-decline

# Reset baseline to current coverage
python coverage_tracker.py --reset-baseline
```

The coverage tracker maintains a baseline in `.coverage_baseline.json` and will:
- ✅ Pass if coverage improves or stays the same
- ⚠️  Warn and fail if coverage declines
- 📝 Update the baseline when coverage improves


⏺ To start the webserver:
  python -m http.server 8080

  To stop it:
  - Press Ctrl+C in the terminal where it's running

  To run it in the background:
  python -m http.server 8080 &

  To stop a background server:
  * Find the process ID
  ps aux | grep "http.server"
  * Kill it using the PID
  kill <PID>

  Or use pkill:
  pkill -f "http.server 8080"
 



