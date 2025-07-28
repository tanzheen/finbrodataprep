"""
Basic tests to verify the test setup is working correctly.
"""

import pytest


def test_basic_import():
    """Test that we can import the main modules."""
    try:
        from main import cli, analyze, batch, info, list_examples
        assert cli is not None
        assert analyze is not None
        assert batch is not None
        assert info is not None
        assert list_examples is not None
    except ImportError as e:
        pytest.fail(f"Failed to import main modules: {e}")


def test_click_commands_exist():
    """Test that Click commands are properly defined."""
    from main import cli
    
    # Check that the CLI group has the expected commands
    # Get command names from the CLI group
    command_names = list(cli.commands.keys())
    expected_commands = ['analyze', 'batch', 'info', 'list-examples']
    
    for cmd in expected_commands:
        assert cmd in command_names, f"Command '{cmd}' not found in CLI"


def test_pytest_working():
    """Test that pytest is working correctly."""
    assert True, "Pytest is working"


def test_coverage_working():
    """Test that coverage is working (this line should be covered)."""
    result = 2 + 2
    assert result == 4


class TestBasicFunctionality:
    """Basic functionality tests."""
    
    def test_string_operations(self):
        """Test basic string operations."""
        text = "Hello, World!"
        assert len(text) == 13
        assert text.upper() == "HELLO, WORLD!"
        assert text.lower() == "hello, world!"
    
    def test_list_operations(self):
        """Test basic list operations."""
        numbers = [1, 2, 3, 4, 5]
        assert len(numbers) == 5
        assert sum(numbers) == 15
        assert max(numbers) == 5
        assert min(numbers) == 1


if __name__ == "__main__":
    pytest.main([__file__]) 