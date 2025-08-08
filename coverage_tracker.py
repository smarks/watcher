#!/usr/bin/env python3
"""
Coverage tracking script that monitors code coverage over time
and warns/fails when coverage declines.
"""

import json
import os
import sys
import subprocess
import re
from datetime import datetime
from typing import Dict, Optional, Tuple


class CoverageTracker:
    """Tracks code coverage over time and prevents regression"""
    
    def __init__(self, baseline_file: str = ".coverage_baseline.json"):
        self.baseline_file = baseline_file
    
    def run_coverage(self) -> Tuple[float, Dict[str, float]]:
        """
        Run pytest with coverage and parse the results
        
        Returns:
            tuple: (total_coverage, per_file_coverage)
        """
        # Run pytest with coverage
        result = subprocess.run([
            "python", "-m", "pytest",
            "--cov=url_watcher", "--cov=sms_notifier",
            "--cov-report=term-missing",
            "--quiet"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode != 0:
            print(f"❌ Tests failed!")
            print(result.stdout)
            print(result.stderr)
            sys.exit(1)
        
        # Parse coverage from output
        output = result.stdout
        total_coverage = self._parse_total_coverage(output)
        per_file_coverage = self._parse_per_file_coverage(output)
        
        return total_coverage, per_file_coverage
    
    def _parse_total_coverage(self, output: str) -> float:
        """Parse total coverage percentage from pytest output"""
        # Look for "TOTAL ... XX%"
        total_match = re.search(r'TOTAL\s+\d+\s+\d+\s+\d+\s+(\d+)%', output)
        if total_match:
            return float(total_match.group(1))
        
        # Fallback: look for any percentage at the end
        percent_match = re.search(r'(\d+)%\s*$', output, re.MULTILINE)
        if percent_match:
            return float(percent_match.group(1))
        
        raise ValueError("Could not parse total coverage from output")
    
    def _parse_per_file_coverage(self, output: str) -> Dict[str, float]:
        """Parse per-file coverage from pytest output"""
        per_file = {}
        
        # Look for lines like "sms_notifier.py      56      0   100%"
        file_matches = re.findall(r'(\w+\.py)\s+\d+\s+\d+\s+(\d+)%', output)
        for filename, coverage in file_matches:
            per_file[filename] = float(coverage)
        
        return per_file
    
    def load_baseline(self) -> Optional[Dict]:
        """Load the baseline coverage data"""
        if not os.path.exists(self.baseline_file):
            return None
        
        try:
            with open(self.baseline_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def save_baseline(self, total_coverage: float, per_file_coverage: Dict[str, float]):
        """Save the current coverage as the new baseline"""
        baseline_data = {
            'timestamp': datetime.now().isoformat(),
            'total_coverage': total_coverage,
            'per_file_coverage': per_file_coverage
        }
        
        with open(self.baseline_file, 'w') as f:
            json.dump(baseline_data, f, indent=2)
    
    def compare_coverage(self, current_total: float, current_per_file: Dict[str, float], 
                        baseline_data: Dict) -> Tuple[bool, str]:
        """
        Compare current coverage with baseline
        
        Returns:
            tuple: (is_acceptable, message)
        """
        baseline_total = baseline_data['total_coverage']
        baseline_per_file = baseline_data.get('per_file_coverage', {})
        
        messages = []
        is_acceptable = True
        
        # Check total coverage
        if current_total < baseline_total:
            diff = baseline_total - current_total
            messages.append(f"⚠️  Total coverage declined: {baseline_total}% → {current_total}% (-{diff}%)")
            is_acceptable = False
        elif current_total > baseline_total:
            diff = current_total - baseline_total
            messages.append(f"✅ Total coverage improved: {baseline_total}% → {current_total}% (+{diff}%)")
        else:
            messages.append(f"📊 Total coverage maintained: {current_total}%")
        
        # Check per-file coverage
        for filename, current_cov in current_per_file.items():
            baseline_cov = baseline_per_file.get(filename, 0)
            
            if current_cov < baseline_cov:
                diff = baseline_cov - current_cov
                messages.append(f"⚠️  {filename}: {baseline_cov}% → {current_cov}% (-{diff}%)")
                is_acceptable = False
            elif current_cov > baseline_cov:
                diff = current_cov - baseline_cov
                messages.append(f"✅ {filename}: {baseline_cov}% → {current_cov}% (+{diff}%)")
        
        return is_acceptable, "\n".join(messages)
    
    def run_check(self, fail_on_decline: bool = True, update_baseline: bool = True) -> bool:
        """
        Run coverage check
        
        Args:
            fail_on_decline: Exit with error code if coverage declines
            update_baseline: Update baseline if coverage improves or maintains
            
        Returns:
            bool: True if coverage is acceptable
        """
        print("🔍 Running coverage check...")
        
        # Run coverage
        current_total, current_per_file = self.run_coverage()
        
        # Load baseline
        baseline_data = self.load_baseline()
        
        if baseline_data is None:
            print("📝 No baseline found, setting current coverage as baseline")
            self.save_baseline(current_total, current_per_file)
            print(f"✅ Baseline set: {current_total}% total coverage")
            return True
        
        # Compare with baseline
        is_acceptable, comparison_message = self.compare_coverage(
            current_total, current_per_file, baseline_data
        )
        
        print("\n" + comparison_message)
        
        # Update baseline if coverage improved or maintained (and update_baseline is True)
        if is_acceptable and update_baseline:
            if current_total >= baseline_data['total_coverage']:
                self.save_baseline(current_total, current_per_file)
                print(f"\n📝 Baseline updated: {current_total}% total coverage")
        
        if not is_acceptable and fail_on_decline:
            print(f"\n❌ Coverage regression detected! Previous: {baseline_data['total_coverage']}%, Current: {current_total}%")
            return False
        
        return True


def main():
    """CLI interface for coverage tracking"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Track code coverage over time")
    parser.add_argument("--fail-on-decline", action="store_true", default=True,
                       help="Exit with error if coverage declines (default: True)")
    parser.add_argument("--no-fail-on-decline", dest="fail_on_decline", action="store_false",
                       help="Don't exit with error if coverage declines")
    parser.add_argument("--update-baseline", action="store_true", default=True,
                       help="Update baseline if coverage improves (default: True)")
    parser.add_argument("--no-update-baseline", dest="update_baseline", action="store_false",
                       help="Don't update baseline")
    parser.add_argument("--reset-baseline", action="store_true",
                       help="Reset the baseline to current coverage")
    
    args = parser.parse_args()
    
    tracker = CoverageTracker()
    
    if args.reset_baseline:
        print("🔄 Resetting baseline...")
        current_total, current_per_file = tracker.run_coverage()
        tracker.save_baseline(current_total, current_per_file)
        print(f"✅ Baseline reset to {current_total}% total coverage")
        return
    
    # Run the check
    success = tracker.run_check(
        fail_on_decline=args.fail_on_decline,
        update_baseline=args.update_baseline
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()