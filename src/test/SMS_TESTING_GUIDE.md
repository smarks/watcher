# SMS Integration Testing Guide

This guide explains how to test your SMS notification setup.

## Prerequisites

1. **Install ClickSend library:**
   ```bash
   pip install clicksend-client
   ```

2. **Set up environment variables:**
   Create a `.env` file in the project root or export these variables:
   ```bash
   export SMS_PHONE_NUMBER="+1234567890"     # Your phone number
   export CLICKSEND_USERNAME="your_username"  # Your ClickSend username
   export CLICKSEND_API_KEY="your_api_key"    # Your ClickSend API key
   export CLICKSEND_SOURCE="URLWatcher"       # Optional: source name
   ```

## Running the Tests

### Option 1: Interactive Mode (Recommended)

This mode prompts you before sending actual SMS messages:

```bash
python src/test/test_sms_integration.py --interactive
```

**What it does:**

- Checks your configuration
- Asks for confirmation before sending SMS
- Runs all three tests sequentially
- Shows detailed results

### Option 2: Standard Test Mode

Run with pytest (will skip if not configured):

```bash
pytest src/test/test_sms_integration.py -v
```

**What it does:**

- Skips tests if SMS is not configured
- Runs tests if configuration is detected
- Part of the normal test suite

### Option 3: Run Individual Tests

Run specific tests directly:

```bash
# Just verify configuration (no SMS sent)
pytest src/test/test_sms_integration.py::TestSMSIntegration::test_verify_setup -v

# Send a test SMS
pytest src/test/test_sms_integration.py::TestSMSIntegration::test_send_test_sms -v

# Send a URL change notification
pytest src/test/test_sms_integration.py::TestSMSIntegration::test_send_url_change_notification -v
```

## Test Descriptions

### Test 1: `test_verify_setup`

- **Purpose:** Verify configuration without sending SMS
- **What it does:** Checks that all credentials are set and valid
- **Cost:** Free (no SMS sent)
- **Use case:** Quick configuration check

### Test 2: `test_send_test_sms`

- **Purpose:** Send an actual test SMS
- **What it does:** Sends a simple test message via ClickSend
- **Cost:** Uses 1 SMS credit
- **Use case:** Verify end-to-end SMS delivery

### Test 3: `test_send_url_change_notification`

- **Purpose:** Send a realistic URL change notification
- **What it does:** Simulates a URL change and sends notification with diff
- **Cost:** Uses 1 SMS credit
- **Use case:** Test the actual notification format

## Example Output

```
======================================================================
SMS INTEGRATION TEST SUITE
======================================================================

This will actually send SMS messages to your configured number.
Make sure you have set the following environment variables:
  - SMS_PHONE_NUMBER
  - CLICKSEND_USERNAME
  - CLICKSEND_API_KEY

Or create a .env file with these variables.

✓ Configuration detected:
  Phone: +1234567890
  Username: your_username
  Source: URLWatcher

⚠️  Continue with SMS tests? This will send actual SMS messages. (yes/no): yes

======================================================================
RUNNING TESTS
======================================================================

test_send_test_sms (__main__.TestSMSIntegration)
Test 2: Actually send a test SMS message ...
======================================================================
SENDING TEST SMS
======================================================================

Sending test SMS to: +1234567890
Source: URLWatcher

----------------------------------------------------------------------
RESULT:
----------------------------------------------------------------------
✅ SUCCESS! Test SMS sent successfully
   Message ID: ABC123456

======================================================================

✅ Check your phone for the test message!

ok
```

## Troubleshooting

### Tests are skipped

**Problem:** Tests show as "SKIPPED"

**Solution:**

- Make sure environment variables are set
- Install clicksend-client: `pip install clicksend-client`
- Verify credentials are correct

### Authentication errors

**Problem:** "Invalid username or password"

**Solution:**

- Double-check CLICKSEND_USERNAME and CLICKSEND_API_KEY
- Log into ClickSend dashboard to verify credentials
- Ensure API key is not expired

### SMS not received

**Problem:** Test passes but no SMS received

**Solution:**

- Check phone number format (must include country code, e.g., +1234567890)
- Verify phone number in ClickSend dashboard
- Check ClickSend account balance
- Look for SMS in ClickSend dashboard logs

## Integration with CI/CD

To skip these tests in CI/CD (to avoid sending SMS on every build):

```bash
# Run all tests except integration tests
pytest --ignore=src/test/test_sms_integration.py

# Or run all tests (integration tests will auto-skip if not configured)
pytest
```

## Cost Considerations

Each test that actually sends an SMS uses ClickSend credits:

- `test_verify_setup`: 0 credits (no SMS sent)
- `test_send_test_sms`: 1 credit
- `test_send_url_change_notification`: 1 credit

Running the full interactive suite: **2 SMS credits**

## Next Steps

After verifying your SMS setup works:

1. Use the verified configuration with `url_watcher.py --sms`
2. Use with `multi_url_watcher.py` for multiple URL monitoring
3. Set up continuous monitoring with confidence
