#!/usr/bin/env python3
"""
Test setup script to verify the basic functionality is working.
"""

import sys
import subprocess


def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import click
        print("✅ Click imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Click: {e}")
        return False
    
    try:
        from main import cli, analyze, batch, info, list_examples
        print("✅ Main modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import main modules: {e}")
        return False
    
    try:
        import pytest
        print("✅ Pytest imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import pytest: {e}")
        return False
    
    return True


def test_click_commands():
    """Test that Click commands are properly defined."""
    print("\n🔍 Testing Click commands...")
    
    try:
        from main import cli
        
        # Check that the CLI group has the expected commands
        command_names = list(cli.commands.keys())
        expected_commands = ['analyze', 'batch', 'info', 'list-examples']
        
        print(f"Found commands: {command_names}")
        
        for cmd in expected_commands:
            if cmd in command_names:
                print(f"✅ Command '{cmd}' found")
            else:
                print(f"❌ Command '{cmd}' not found")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing Click commands: {e}")
        return False


def test_basic_pytest():
    """Test that pytest can run basic tests."""
    print("\n🔍 Testing pytest...")
    
    try:
        # Run a simple test
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_basic.py::test_pytest_working", "-q"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Pytest is working correctly")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Pytest failed: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error running pytest: {e}")
        return False


def test_cli_help():
    """Test that the CLI help works."""
    print("\n🔍 Testing CLI help...")
    
    try:
        result = subprocess.run(
            ["python", "main.py", "--help"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if "Stock Analysis Pipeline" in result.stdout:
            print("✅ CLI help works correctly")
            return True
        else:
            print("❌ CLI help output doesn't contain expected content")
            return False
    except subprocess.CalledProcessError as e:
        print(f"❌ CLI help failed: {e}")
        return False


def main():
    """Run all setup tests."""
    print("🚀 Testing Stock Analysis Pipeline Setup")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Click Commands", test_click_commands),
        ("Pytest", test_basic_pytest),
        ("CLI Help", test_cli_help),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test passed")
        else:
            print(f"❌ {test_name} test failed")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Setup is working correctly.")
        print("\nYou can now run:")
        print("  python main.py --help")
        print("  python run_tests.py")
        return True
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 