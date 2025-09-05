#!/usr/bin/env python3
"""Test the countdown timer functionality"""

# import sys  # noqa: F401
import time


def demo_countdown():
    """Demo the countdown timer"""
    wait_time = 10  # 10 seconds for demo

    print(f"Starting countdown demo for {wait_time} seconds...")
    print("Watch how the timer updates on the same line:")

    # Countdown timer - update every second
    for remaining in range(wait_time, 0, -1):
        # Use \r to overwrite the same line
        minutes, seconds = divmod(remaining, 60)
        time_str = f"{minutes:02d}:{seconds:02d}" if minutes > 0 else f"{seconds} seconds"
        print(f"\rNext check in: {time_str}  ", end="", flush=True)
        time.sleep(1)

    # Clear the countdown line
    print("\r" + " " * 50 + "\r", end="")
    print("✅ Countdown complete!")


if __name__ == "__main__":
    demo_countdown()
