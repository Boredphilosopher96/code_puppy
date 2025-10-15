"""Test UserOnlyHistory filtering behavior."""
from unittest.mock import MagicMock

from code_puppy.command_line.prompt_toolkit_completion import UserOnlyHistory


def test_user_only_history_filters_system_generated_prompts():
    """Test that UserOnlyHistory filters out system-generated prompts."""
    # Create a mock FileHistory
    mock_file_history = MagicMock()
    
    # Simulate history entries with both user commands and system-generated prompts
    history_entries = [
        "/help",  # User command
        "explain this code",  # User prompt
        "Generate a comprehensive PR description for my current branch changes. Follow these steps:\n\n 1 Discover the changes: Use git CLI to find the base branch (usually main/master/develop) and get the list of changed files, commits, and diffs.\n 2 Analyze the code: Read and analyze all modified files to understand:\n    • What functionality was added/changed/removed\n    • The technical approach and implementation details",  # System-generated (long multi-line)
        "/cd /tmp",  # User command
        "1. Discover the base branch\n2. Analyze code\n3. Generate structured description\n4. Create markdown file\n5. Make it review-ready\n6. Update PR if possible\n7. More steps\n8. Even more\n9. Keep going\n10. Almost there\n11. Still more\n12. Final step",  # System-generated (many lines)
    ]
    
    mock_file_history.load_history_strings.return_value = iter(history_entries)
    
    # Create UserOnlyHistory wrapper
    user_history = UserOnlyHistory(mock_file_history)
    
    # Load history and filter
    filtered_entries = list(user_history.load_history_strings())
    
    # Should only have user commands/prompts, not system-generated ones
    assert "/help" in filtered_entries
    assert "explain this code" in filtered_entries
    assert "/cd /tmp" in filtered_entries
    
    # System-generated prompts should be filtered out
    assert not any("Generate a comprehensive" in entry for entry in filtered_entries)
    assert not any("1. Discover the base branch" in entry for entry in filtered_entries)
    
    # Should have 3 user entries
    assert len(filtered_entries) == 3


def test_user_only_history_stores_only_user_input():
    """Test that UserOnlyHistory only stores user-generated input."""
    mock_file_history = MagicMock()
    user_history = UserOnlyHistory(mock_file_history)
    
    # Store a normal user command
    user_history.store_string("/help")
    mock_file_history.store_string.assert_called_once_with("/help")
    
    # Reset mock
    mock_file_history.reset_mock()
    
    # Store a system-generated prompt (should be filtered)
    long_prompt = "Generate a comprehensive PR description for my current branch changes. Follow these steps:\n\n" * 20
    user_history.store_string(long_prompt)
    # Should NOT be stored because it's system-generated
    mock_file_history.store_string.assert_not_called()


def test_user_only_history_detects_system_prompts():
    """Test the _is_system_generated heuristic."""
    mock_file_history = MagicMock()
    user_history = UserOnlyHistory(mock_file_history)
    
    # User commands/prompts should not be detected as system-generated
    assert not user_history._is_system_generated("/help")
    assert not user_history._is_system_generated("explain this code")
    assert not user_history._is_system_generated("/cd /tmp")
    assert not user_history._is_system_generated("what does this function do?")
    
    # System-generated prompts should be detected
    long_multiline = "line\n" * 15  # More than 10 newlines
    assert user_history._is_system_generated(long_multiline)
    
    system_prompt = "Generate a comprehensive report on the following topics..."
    assert user_history._is_system_generated(system_prompt)
    
    numbered_steps = "Follow these steps:\n1. Discover\n2. Analyze\n3. Generate"
    assert user_history._is_system_generated(numbered_steps)


def test_user_only_history_user_input_mode():
    """Test the user input mode toggle."""
    mock_file_history = MagicMock()
    user_history = UserOnlyHistory(mock_file_history)
    
    # Initially in user input mode
    assert user_history._user_input_mode is True
    
    # Storing in user mode works
    user_history.store_string("test command")
    mock_file_history.store_string.assert_called_once_with("test command")
    
    # Switch to non-user mode
    user_history.set_user_input_mode(False)
    assert user_history._user_input_mode is False
    
    # Reset mock
    mock_file_history.reset_mock()
    
    # Storing in non-user mode should not save
    user_history.store_string("another command")
    mock_file_history.store_string.assert_not_called()
    
    # Switch back to user mode
    user_history.set_user_input_mode(True)
    assert user_history._user_input_mode is True
    
    # Now it should work again
    user_history.store_string("final command")
    mock_file_history.store_string.assert_called_once_with("final command")

