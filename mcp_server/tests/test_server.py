"""
Unit tests for the MCP server implementation.
"""

import asyncio
import json

# Import the server module
import sys
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_server.server.main import _INFO_DOC_PATH, get_info, execute_python_code


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


class TestExecutePythonCodeTool:
    """Test cases for the execute_python_code tool."""

    @pytest.mark.asyncio
    async def test_execute_python_code_missing_pptx_library(self):
        """Test handling when python-pptx library is not available."""
        with patch('mcp_server.server.main.pptx', None):
            result = await execute_python_code("print('test')", "test.pptx")
            
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "python-pptx library is not available" in result_data["error"]
        assert result_data["stdout"] == ""
        assert result_data["stderr"] == ""

    @pytest.mark.asyncio
    async def test_execute_python_code_file_not_found(self):
        """Test handling when presentation file doesn't exist."""
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=False):
                result = await execute_python_code("print('test')", "nonexistent.pptx")
                
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "File not found" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_invalid_file_type(self):
        """Test handling when file is not a .pptx file."""
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.txt')):
                    result = await execute_python_code("print('test')", "test.txt")
                    
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Invalid file type" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_path_traversal_attempt(self):
        """Test security against path traversal attempts."""
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    # Mock resolve to return path with ..
                    with patch('pathlib.Path.resolve', return_value=Path("../../../etc/passwd.pptx")):
                        result = await execute_python_code("print('test')", "../../../etc/passwd.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "path traversal not allowed" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_presentation_load_error(self):
        """Test handling when presentation fails to load."""
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.side_effect = Exception("Corrupted file")
                    result = await execute_python_code("print('test')", "test.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Failed to load presentation" in result_data["error"]
        assert "Corrupted file" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_syntax_error(self):
        """Test handling of syntax errors in provided code."""
        mock_presentation = object()
        
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.return_value = mock_presentation
                    
                    # Provide invalid Python syntax
                    result = await execute_python_code("if True print('test')", "test.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Syntax error in Python code" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_runtime_error(self):
        """Test handling of runtime errors in provided code."""
        mock_presentation = object()
        
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.return_value = mock_presentation
                    
                    # Provide code that will cause a runtime error
                    result = await execute_python_code("raise ValueError('test error')", "test.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "Runtime error" in result_data["error"]
        assert "test error" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_successful_execution_with_stdout(self):
        """Test successful execution with stdout capture."""
        mock_presentation = object()
        
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.return_value = mock_presentation
                    
                    code = "print('Hello from Python!')\nprint('Second line')"
                    result = await execute_python_code(code, "test.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "Hello from Python!" in result_data["stdout"]
        assert "Second line" in result_data["stdout"]
        assert result_data["error"] is None

    @pytest.mark.asyncio
    async def test_execute_python_code_prs_object_available(self):
        """Test that the prs object is available in execution context."""
        from unittest.mock import MagicMock
        mock_presentation = MagicMock()
        mock_presentation.slides = ["slide1", "slide2"]  # Mock slides
        
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.return_value = mock_presentation
                    
                    code = "print(f'Slides: {len(prs.slides)}')"
                    result = await execute_python_code(code, "test.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "Slides: 2" in result_data["stdout"]

    @pytest.mark.asyncio
    async def test_execute_python_code_has_execution_time(self):
        """Test that execution time is included in results."""
        mock_presentation = object()
        
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.return_value = mock_presentation
                    
                    result = await execute_python_code("print('test')", "test.pptx")
                    
        result_data = json.loads(result)
        assert "execution_time" in result_data
        assert isinstance(result_data["execution_time"], float)
        assert result_data["execution_time"] >= 0

    @pytest.mark.asyncio
    async def test_execute_python_code_stderr_capture(self):
        """Test that stderr is captured correctly."""
        mock_presentation = object()
        
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.suffix', new_callable=lambda: property(lambda self: '.pptx')):
                    mock_pptx.Presentation.return_value = mock_presentation
                    
                    code = """
import sys
print('This goes to stdout')
print('This goes to stderr', file=sys.stderr)
"""
                    result = await execute_python_code(code, "test.pptx")
                    
        result_data = json.loads(result)
        assert result_data["success"] is True
        assert "This goes to stdout" in result_data["stdout"]
        assert "This goes to stderr" in result_data["stderr"]
