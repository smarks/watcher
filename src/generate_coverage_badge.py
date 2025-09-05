#!/usr/bin/env python3
"""
Generate a simple coverage badge for README
"""
import os
import re
import subprocess


def get_current_coverage():
    """Get current coverage percentage"""
    try:
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "--cov=.",
                "--cov-report=term-missing",
                "--quiet",
            ],
            capture_output=True,
            text=True,
        )
        match = re.search(r"TOTAL.*?(\d+)%", result.stdout)
        return float(match.group(1)) if match else 0
    except Exception:
        return 0


def generate_badge_url(coverage):
    """Generate shields.io badge URL"""
    color = "red"
    if coverage >= 90:
        color = "brightgreen"
    elif coverage >= 80:
        color = "green"
    elif coverage >= 70:
        color = "yellow"
    elif coverage >= 60:
        color = "orange"

    return f"https://img.shields.io/badge/coverage-{coverage}%25-{color}"


def main():
    coverage = get_current_coverage()
    badge_url = generate_badge_url(coverage)

    print(f"Current coverage: {coverage}%")
    print(f"Badge URL: {badge_url}")
    print(f"Markdown: ![Coverage]({badge_url})")

    # Save to file for GitHub Actions
    if os.environ.get("GITHUB_ACTIONS"):
        with open("coverage_badge.md", "w") as f:
            f.write(f"![Coverage]({badge_url})\n")
        print("Badge markdown saved to coverage_badge.md")


if __name__ == "__main__":
    main()
