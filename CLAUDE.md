# Claude Code Configuration

This file contains configuration and context for Claude Code to better assist with this project.

## Project Overview
URL Watcher - A Python application that monitors URLs for changes and sends SMS notifications when changes are detected.

## Development Commands
- Test: `python -m pytest`
- Lint: `flake8 . && black --check .`
- Format: `black .`
- Coverage: `python -m pytest --cov=. --cov-report=term-missing`
- Start: `python url_watcher.py --url <URL> --interval <seconds>`

## Project Structure
- `url_watcher.py` - Main application for monitoring URLs
- `sms_notifier.py` - SMS notification module using TextBelt API
- `coverage_tracker.py` - Coverage tracking and baseline management
- `test_*.py` - Unit test files
- `.flake8` - Flake8 linter configuration
- `pyproject.toml` - Black formatter and project configuration

## Important Notes
- Always run linting before committing: `flake8 . && black --check .`
- Use black for formatting: `black .`
- Max line length is configured to 100 characters
- SMS notifications require TEXTBELT_API_KEY and SMS_PHONE_NUMBER environment variables