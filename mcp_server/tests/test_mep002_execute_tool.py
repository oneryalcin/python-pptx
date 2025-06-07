"""
Unit tests for MEP-002: execute_python_code Tool (Updated for MEP-003).

Tests the execute_python_code tool functionality with the updated signature
that uses pre-loaded presentations from client roots instead of file_path parameter.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from mcp_server.server.tools import execute_python_code


class TestExecutePythonCodeTool:
    """Test cases for the execute_python_code tool with MEP-003 changes."""

    @pytest.mark.asyncio
    async def test_execute_python_code_missing_pptx_library(self):
        """Test execute_python_code when pptx library is not available."""
        with patch('mcp_server.server.tools.pptx', None):
            result = await execute_python_code("print('test')")
            
            result_data = json.loads(result)
            assert result_data["success"] is False
            assert "python-pptx library is not available" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_no_presentation_loaded(self):
        """Test execute_python_code with no presentation loaded."""
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with no presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = None
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code("print('test')")
                
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "No PowerPoint presentation loaded" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_syntax_error(self):
        """Test execute_python_code with Python syntax error."""
        mock_presentation = Mock()
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = mock_presentation
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code("if True print('test')")
                
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "Syntax error" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_runtime_error(self):
        """Test execute_python_code with Python runtime error."""
        mock_presentation = Mock()
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = mock_presentation
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code("raise ValueError('test error')")
                
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "Runtime error" in result_data["error"]
                assert "test error" in result_data["error"]

    @pytest.mark.asyncio
    async def test_execute_python_code_successful_execution_with_stdout(self):
        """Test execute_python_code with successful execution that produces stdout."""
        mock_presentation = Mock()
        code = """
print("Line 1")
print("Line 2")
result = 2 + 2
print(f"Result: {result}")
"""
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = mock_presentation
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code(code)
                
                result_data = json.loads(result)
                assert result_data["success"] is True
                assert "Line 1" in result_data["stdout"]
                assert "Line 2" in result_data["stdout"]
                assert "Result: 4" in result_data["stdout"]
                assert result_data["error"] is None

    @pytest.mark.asyncio
    async def test_execute_python_code_prs_object_available(self):
        """Test that the prs object is available in the execution context."""
        mock_presentation = Mock()
        mock_presentation.slides = []  # Mock slides attribute
        
        code = """
# Test that prs object is available
print(f"Presentation type: {type(prs)}")
print(f"Slide count: {len(prs.slides)}")
"""
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = mock_presentation
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code(code)
                
                result_data = json.loads(result)
                assert result_data["success"] is True
                assert "Presentation type:" in result_data["stdout"]
                assert "Slide count: 0" in result_data["stdout"]

    @pytest.mark.asyncio
    async def test_execute_python_code_has_execution_time(self):
        """Test that execute_python_code includes execution time in results."""
        mock_presentation = Mock()
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = mock_presentation
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code("print('test')")
                
                result_data = json.loads(result)
                assert "execution_time" in result_data
                assert isinstance(result_data["execution_time"], (int, float))
                assert result_data["execution_time"] >= 0

    @pytest.mark.asyncio
    async def test_execute_python_code_stderr_capture(self):
        """Test that execute_python_code captures stderr output."""
        mock_presentation = Mock()
        code = """
import sys
print("This goes to stdout")
print("This goes to stderr", file=sys.stderr)
"""
        with patch('mcp_server.server.tools.pptx', Mock()):
            # Mock session with presentation loaded
            mock_session = Mock()
            mock_session.loaded_presentation = mock_presentation
            with patch('mcp_server.server.tools.get_session', return_value=mock_session):
                result = await execute_python_code(code)
                
                result_data = json.loads(result)
                assert result_data["success"] is True
                assert "This goes to stdout" in result_data["stdout"]
                assert "This goes to stderr" in result_data["stderr"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])