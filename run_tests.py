#!/usr/bin/env python3
"""
Test runner for the Stock Analysis Pipeline

This script provides an easy way to run tests with different options.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_tests(test_path: str = None, verbose: bool = False, coverage: bool = True):
    """
    Run the test suite.
    
    Args:
        test_path: Specific test file or directory to run
        verbose: Whether to run in verbose mode
        coverage: Whether to generate coverage reports
    """
    cmd = ["python", "-m", "pytest"]
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append("tests/")
    
    if verbose:
        cmd.append("-v")
    
    # Coverage is configured in pyproject.toml, so we don't need to add it here
    # The configuration will be automatically applied
    
    print(f"Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False


def run_specific_test(test_name: str):
    """Run a specific test by name."""
    cmd = ["python", "-m", "pytest", f"tests/main_tests.py::{test_name}", "-v"]
    
    print(f"Running specific test: {test_name}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ Test {test_name} passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test {test_name} failed!")
        return False


def list_tests():
    """List all available tests."""
    cmd = ["python", "-m", "pytest", "tests/", "--collect-only", "-q"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        tests = result.stdout.strip().split('\n')
        
        print("📋 Available Tests:")
        print("=" * 30)
        
        for test in tests:
            if test and not test.startswith('='):
                print(f"  {test}")
        
        print(f"\nTotal: {len([t for t in tests if t and not t.startswith('=')])} tests")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing tests: {e}")


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Test runner for Stock Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests with coverage
  python run_tests.py --no-coverage     # Run tests without coverage
  python run_tests.py --verbose         # Run tests in verbose mode
  python run_tests.py --test TestAnalyzeCommand::test_analyze_success
  python run_tests.py --list            # List all available tests
        """
    )
    
    parser.add_argument(
        "--test",
        type=str,
        help="Run a specific test by name"
    )
    
    parser.add_argument(
        "--path",
        type=str,
        help="Run tests from specific file or directory"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Run tests in verbose mode"
    )
    
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Run tests without coverage reporting"
    )
    
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available tests"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_tests()
        return
    
    if args.test:
        success = run_specific_test(args.test)
    else:
        # For now, coverage is always enabled via pyproject.toml
        # The --no-coverage flag is kept for future use
        success = run_tests(
            test_path=args.path,
            verbose=args.verbose,
            coverage=True  # Always enabled via pyproject.toml
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 