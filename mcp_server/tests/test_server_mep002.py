"""
Unit tests for the MEP-002 (original) MCP server implementation.
These tests are preserved to ensure backward compatibility understanding.
"""

import asyncio
import json

# Import the server module
import sys
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock, mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_server.server.main import _INFO_DOC_PATH, get_info


class TestGetInfoTool:
    """Test cases for the get_info tool."""

    @pytest.mark.asyncio
    async def test_get_info_success(self):
        """Test successful reading of info document."""
        mock_content = "# Test Content\nThis is a test markdown file."

        with patch("builtins.open", mock_open(read_data=mock_content)):
            result = await get_info()

        assert result == mock_content
        assert "# Test Content" in result
        assert "This is a test markdown file." in result

    @pytest.mark.asyncio
    async def test_get_info_file_not_found(self):
        """Test handling when info document doesn't exist."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            result = await get_info()

        assert "# Error: Information document not found" in result
        assert str(_INFO_DOC_PATH) in result

    @pytest.mark.asyncio
    async def test_get_info_permission_error(self):
        """Test handling when permission is denied."""
        with patch("builtins.open", side_effect=PermissionError):
            result = await get_info()

        assert "# Error: Permission denied reading information document." in result

    @pytest.mark.asyncio
    async def test_get_info_unicode_decode_error(self):
        """Test handling when file has encoding issues."""
        with patch("builtins.open", side_effect=UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")):
            result = await get_info()

        assert "# Error: Could not decode information document (encoding issue)." in result

    @pytest.mark.asyncio
    async def test_get_info_empty_file(self):
        """Test handling when info document is empty."""
        with patch("builtins.open", mock_open(read_data="")):
            result = await get_info()

        assert "# Error: Information document is empty." in result

    @pytest.mark.asyncio
    async def test_get_info_whitespace_only_file(self):
        """Test handling when info document contains only whitespace."""
        with patch("builtins.open", mock_open(read_data="   \n\t\n   ")):
            result = await get_info()

        assert "# Error: Information document is empty." in result

    @pytest.mark.asyncio
    async def test_get_info_generic_exception(self):
        """Test handling of unexpected exceptions."""
        with patch("builtins.open", side_effect=IOError("Unexpected error")):
            result = await get_info()

        assert "# Error: Could not read information document." in result
        assert "Unexpected error" in result


class TestServerConfiguration:
    """Test cases for server configuration and structure."""

    def test_info_doc_path_exists(self):
        """Test that the info document path is correctly defined."""
        expected_path = Path(__file__).parent.parent / "llm_info.md"
        assert expected_path == _INFO_DOC_PATH

    def test_info_doc_path_relative_structure(self):
        """Test that the path structure is correct relative to main.py."""
        # The path should point to mcp_server/llm_info.md from mcp_server/server/main.py
        assert _INFO_DOC_PATH.name == "llm_info.md"
        assert _INFO_DOC_PATH.parent.name == "mcp_server"


class TestAsyncFunctionality:
    """Test cases to ensure async functionality works correctly."""

    @pytest.mark.asyncio
    async def test_get_info_is_coroutine(self):
        """Test that get_info returns a coroutine."""
        with patch("builtins.open", mock_open(read_data="test")):
            result = get_info()
            assert asyncio.iscoroutine(result)
            await result  # Clean up the coroutine


# Note: MEP-002 execute_python_code tests are intentionally commented out
# as they used the old signature with file_path parameter.
# See test_mep003.py for updated tests with the new signature.