#!/usr/bin/env python3
"""
Test script for URL watcher functionality
"""

import os
import time

import requests

from url_watcher import URLWatcher


def test_local_server():
    """Test if local server is accessible"""
    print("Testing local server accessibility...")
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        print(f"✅ Server accessible - Status: {response.status_code}")
        print(f"Content preview: {response.text[:100]}...")
        return True
    except requests.RequestException as e:
        print(f"❌ Server not accessible: {e}")
        return False


def test_single_check():
    """Test single URL check"""
    print("\nTesting single URL check...")
    watcher = URLWatcher("test_cache.json")

    try:
        changed, difference = watcher.check_url("http://localhost:8080")
        print(f"First check - Changed: {changed}")
        if difference:
            print(f"Message: {difference}")

        # Second check should show no changes
        changed, difference = watcher.check_url("http://localhost:8080")
        print(f"Second check - Changed: {changed}")
        return True
    except Exception as e:
        print(f"❌ Single check failed: {e}")
        return False


def test_continuous_monitoring():
    """Test continuous monitoring with short intervals"""
    print("\nTesting continuous monitoring (5 second intervals)...")
    print("This will run for 30 seconds, then stop...")

    watcher = URLWatcher("test_cache_continuous.json")

    try:
        # Start monitoring in background for a short time
        start_time = time.time()
        check_count = 0

        while time.time() - start_time < 30:  # Run for 30 seconds
            print(f"\n[Check {check_count + 1}] {time.strftime('%H:%M:%S')}")
            changed, difference = watcher.check_url("http://localhost:8080")

            if changed:
                print("✅ Content changed!")
                if difference:
                    print("Difference detected")
            else:
                print("❌ No changes")

            check_count += 1
            time.sleep(5)  # 5 second intervals for testing

        print(f"\n✅ Continuous monitoring test completed ({check_count} checks)")
        return True

    except Exception as e:
        print(f"❌ Continuous monitoring failed: {e}")
        return False


def cleanup():
    """Clean up test files"""
    test_files = ["test_cache.json", "test_cache_continuous.json"]
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up {file}")


def main():
    print("URL Watcher Test Suite")
    print("=" * 40)

    results = []

    # Test 1: Server accessibility
    results.append(("Server Access", test_local_server()))

    # Test 2: Single check
    results.append(("Single Check", test_single_check()))

    # Test 3: Continuous monitoring
    results.append(("Continuous Monitoring", test_continuous_monitoring()))

    # Cleanup
    cleanup()

    # Summary
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")

    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nPassed: {total_passed}/{len(results)} tests")


if __name__ == "__main__":
    main()
