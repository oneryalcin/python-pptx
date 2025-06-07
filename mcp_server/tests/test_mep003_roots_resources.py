#!/usr/bin/env python3
"""
Unit tests for MEP-003: Root Management and Resource Discovery.

Tests the root management, presentation auto-loading, and resource endpoints.
This covers the root handling and resource discovery implemented in MEP-003.

NOTE: Many complex tests have been temporarily commented out during the refactoring
to the new session-based architecture. These tests should be rewritten to use the
new session management system.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
import sys

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the server module
try:
    from mcp_server.server.session import (
        set_client_roots, 
        load_presentation,
        get_session,
    )
    from mcp_server.server.tools import (
        execute_python_code,
        get_presentation_tree
    )
    from mcp import types
except ImportError as e:
    pytest.skip(f"Could not import server module: {e}", allow_module_level=True)


class TestRootManagement:
    """Test root handling and presentation loading functionality."""
    
    def test_set_client_roots_empty_list(self):
        """Test setting empty roots list."""
        set_client_roots([])
        
        # Should clear any loaded presentation  
        session = get_session()
        assert session.loaded_presentation is None
        assert session.loaded_presentation_path is None
    
    def test_set_client_roots_with_pptx_file(self):
        """Test setting roots with a .pptx file."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions
        clear_session_store()
        
        with patch('mcp_server.server.session.pptx') as mock_pptx:
            mock_presentation = Mock()
            mock_pptx.Presentation.return_value = mock_presentation
            
            # Create a root pointing directly to a .pptx file
            test_file = Path("/test/presentation.pptx")
            roots = [types.Root(uri=f"file://{test_file}")]
            
            with patch.object(Path, 'exists', return_value=True), \
                 patch.object(Path, 'is_file', return_value=True), \
                 patch.object(Path, 'suffix', '.pptx'):
                
                set_client_roots(roots)
                
                # Verify presentation was loaded
                session = get_session()
                assert session.loaded_presentation is not None
                assert session.loaded_presentation_path == test_file
                mock_pptx.Presentation.assert_called_once_with(test_file)
    
    def test_set_client_roots_with_directory(self):
        """Test setting roots with directory containing .pptx files."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions
        clear_session_store()
        
        with patch('mcp_server.server.session.pptx') as mock_pptx:
            mock_presentation = Mock()
            mock_pptx.Presentation.return_value = mock_presentation
            
            # Create a root pointing to a directory with .pptx files
            test_dir = Path("/test/directory")
            test_file = Path("/test/directory/presentation.pptx")
            roots = [types.Root(uri=f"file://{test_dir}")]
            
            with patch.object(Path, 'exists', return_value=True), \
                 patch.object(Path, 'is_file', return_value=False), \
                 patch.object(Path, 'is_dir', return_value=True), \
                 patch.object(Path, 'glob', return_value=[test_file]):
                
                set_client_roots(roots)
                
                # Verify presentation was loaded from the directory
                session = get_session()
                assert session.loaded_presentation is not None
                assert session.loaded_presentation_path == test_file
                mock_pptx.Presentation.assert_called_once_with(test_file)
    
    def test_load_presentation_success(self):
        """Test successful presentation loading."""
        with patch('mcp_server.server.session.pptx') as mock_pptx:
            mock_presentation = Mock()
            mock_pptx.Presentation.return_value = mock_presentation
            mock_pptx.is_not_none = True
            
            test_file = Path("/test/presentation.pptx")
            result = load_presentation(test_file)
            
            assert result is True
            mock_pptx.Presentation.assert_called_once_with(test_file)
    
    def test_load_presentation_no_pptx_library(self):
        """Test presentation loading when pptx library is not available."""
        with patch('mcp_server.server.session.pptx', None):
            test_file = Path("/test/presentation.pptx")
            result = load_presentation(test_file)
            
            assert result is False


class TestExecutePythonCodeTool:
    """Test the refactored execute_python_code tool."""
    
    @pytest.mark.asyncio
    async def test_execute_python_code_no_pptx_library(self):
        """Test execute_python_code when pptx library is not available."""
        with patch('mcp_server.server.tools.pptx', None):
            result = await execute_python_code("print('test')")
            
            data = json.loads(result)
            assert data["success"] is False
            assert "python-pptx library is not available" in data["error"]
            assert "execution_time" in data

    @pytest.mark.asyncio
    async def test_execute_python_code_no_presentation_loaded(self):
        """Test execute_python_code when no presentation is loaded."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions
        clear_session_store()
        
        with patch('mcp_server.server.tools.pptx', MagicMock()):
            result = await execute_python_code("print('test')")
            
            data = json.loads(result)
            assert data["success"] is False
            assert "No PowerPoint presentation loaded" in data["error"]
            assert "execution_time" in data

    @pytest.mark.asyncio
    async def test_execute_python_code_success(self):
        """Test successful Python code execution."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session with loaded presentation
        clear_session_store()
        
        with patch('mcp_server.server.tools.pptx', MagicMock()) as mock_pptx, \
             patch('mcp_server.server.tools.get_session') as mock_get_session:
            
            # Create a mock session with a loaded presentation
            mock_session = Mock()
            mock_presentation = Mock()
            mock_session.loaded_presentation = mock_presentation
            mock_get_session.return_value = mock_session
            
            result = await execute_python_code("print('Hello, World!')")
            
            data = json.loads(result)
            assert data["success"] is True
            assert "Hello, World!" in data["stdout"]
            assert data["error"] is None
            assert "execution_time" in data

    @pytest.mark.asyncio
    async def test_execute_python_code_syntax_error(self):
        """Test execute_python_code with syntax error."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.pptx', MagicMock()) as mock_pptx, \
             patch('mcp_server.server.tools.get_session') as mock_get_session:
            
            # Create a mock session with a loaded presentation
            mock_session = Mock()
            mock_presentation = Mock()
            mock_session.loaded_presentation = mock_presentation
            mock_get_session.return_value = mock_session
            
            # Execute code with syntax error
            result = await execute_python_code("print('unterminated string)")
            
            data = json.loads(result)
            assert data["success"] is False
            assert "Syntax error in Python code" in data["error"]
            assert "execution_time" in data

    @pytest.mark.asyncio
    async def test_execute_python_code_runtime_error(self):
        """Test execute_python_code with runtime error."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.pptx', MagicMock()) as mock_pptx, \
             patch('mcp_server.server.tools.get_session') as mock_get_session:
            
            # Create a mock session with a loaded presentation
            mock_session = Mock()
            mock_presentation = Mock()
            mock_session.loaded_presentation = mock_presentation
            mock_get_session.return_value = mock_session
            
            # Execute code that will cause a runtime error
            result = await execute_python_code("1 / 0")
            
            data = json.loads(result)
            assert data["success"] is False
            assert "Runtime error" in data["error"]
            assert "division by zero" in data["error"]
            assert "execution_time" in data


class TestResourceHandlers:
    """Test resource functionality."""
    
    @pytest.mark.asyncio
    async def test_get_presentation_tree_no_presentation(self):
        """Test get_presentation_tree when no presentation is loaded."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions
        clear_session_store()
        
        result = await get_presentation_tree()
        
        data = json.loads(result)
        assert "error" in data
        assert "No presentation loaded" in data["error"]
        assert "session_id" in data

    @pytest.mark.asyncio
    async def test_get_presentation_tree_with_get_tree(self):
        """Test get_presentation_tree when presentation has get_tree method."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.get_session') as mock_get_session:
            # Create a mock session with a loaded presentation that has get_tree method
            mock_session = Mock()
            mock_presentation = Mock()
            mock_tree_data = {"type": "presentation", "slides": [{"title": "Test Slide"}]}
            mock_presentation.get_tree.return_value = mock_tree_data
            mock_session.loaded_presentation = mock_presentation
            mock_session.loaded_presentation_path = Path("/test/presentation.pptx")
            mock_get_session.return_value = mock_session
            
            result = await get_presentation_tree()
            
            data = json.loads(result)
            assert data == mock_tree_data
            mock_presentation.get_tree.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_presentation_tree_without_get_tree(self):
        """Test get_presentation_tree when presentation doesn't have get_tree method."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.get_session') as mock_get_session:
            # Create a mock session with a loaded presentation without get_tree method
            mock_session = Mock()
            mock_presentation = Mock()
            mock_slides = [Mock(), Mock()]  # Mock 2 slides
            mock_presentation.slides = mock_slides
            # Ensure get_tree attribute doesn't exist
            del mock_presentation.get_tree
            mock_session.loaded_presentation = mock_presentation
            mock_session.loaded_presentation_path = Path("/test/presentation.pptx")
            mock_session.session_id = "test-session-123"
            mock_get_session.return_value = mock_session
            
            result = await get_presentation_tree()
            
            data = json.loads(result)
            assert data["type"] == "presentation"
            assert data["slide_count"] == 2
            assert data["file_path"] == "/test/presentation.pptx"
            assert data["session_id"] == "test-session-123"
            assert "get_tree() method not available" in data["note"]

    @pytest.mark.asyncio
    async def test_get_presentation_tree_error(self):
        """Test get_presentation_tree when get_tree method raises an error."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.get_session') as mock_get_session:
            # Create a mock session with a loaded presentation where get_tree raises an error
            mock_session = Mock()
            mock_presentation = Mock()
            mock_slides = [Mock()]  # Mock 1 slide
            mock_presentation.slides = mock_slides
            mock_presentation.get_tree.side_effect = Exception("Tree generation failed")
            mock_session.loaded_presentation = mock_presentation
            mock_session.loaded_presentation_path = Path("/test/presentation.pptx")
            mock_session.session_id = "test-session-123"
            mock_get_session.return_value = mock_session
            
            result = await get_presentation_tree()
            
            data = json.loads(result)
            assert data["type"] == "presentation"
            assert data["slide_count"] == 1
            assert data["file_path"] == "/test/presentation.pptx"
            assert data["session_id"] == "test-session-123"
            assert "Failed to get tree data: Tree generation failed" in data["error"]


class TestSessionManagement:
    """Test session management and cleanup functionality."""
    
    def test_session_cleanup(self):
        """Test that expired sessions are properly cleaned up."""
        from mcp_server.server.session import (
            clear_session_store, get_session_store, cleanup_expired_sessions
        )
        import time
        
        # Clear any existing sessions
        clear_session_store()
        
        # Create a session by calling get_session
        session = get_session()
        original_session_id = session.session_id
        
        # Verify session exists
        session_store = get_session_store()
        assert original_session_id in session_store
        
        # Manually set the last_accessed time to be old (more than 1 hour ago)
        session_store[original_session_id].last_accessed = time.time() - 3700  # 61+ minutes ago
        
        # Call cleanup with 1 hour max age
        cleanup_expired_sessions(max_age=3600)
        
        # Verify session was cleaned up
        assert original_session_id not in session_store
    
    def test_multiple_sessions(self):
        """Test that multiple sessions can coexist."""
        from mcp_server.server.session import (
            clear_session_store, get_session_store, SessionContext
        )
        from mcp import types
        import time
        
        # Clear any existing sessions
        clear_session_store()
        
        # Manually create multiple sessions to simulate different clients
        session_store = get_session_store()
        session1 = SessionContext(
            session_id="client-1",
            created_at=time.time(),
            last_accessed=time.time(),
            client_roots=[types.Root(uri="file:///client1/root")]
        )
        session2 = SessionContext(
            session_id="client-2", 
            created_at=time.time(),
            last_accessed=time.time(),
            client_roots=[types.Root(uri="file:///client2/root")]
        )
        
        session_store["client-1"] = session1
        session_store["client-2"] = session2
        
        # Verify both sessions exist with different roots
        assert len(session_store) == 2
        assert str(session_store["client-1"].client_roots[0].uri) == "file:///client1/root"
        assert str(session_store["client-2"].client_roots[0].uri) == "file:///client2/root"
    
    def test_set_client_roots_invalid_uri(self):
        """Test set_client_roots with invalid URI formats."""
        from mcp_server.server.session import clear_session_store
        import pytest
        from pydantic_core import ValidationError
        
        # Clear any existing sessions
        clear_session_store()
        
        # Test that Root validation rejects non-file URIs (this is correct behavior)
        with pytest.raises(ValidationError) as exc_info:
            invalid_roots = [types.Root(uri="http://invalid.com/file.pptx")]
        
        # Verify the validation error is about URL scheme
        assert "URL scheme should be 'file'" in str(exc_info.value)
        
        # Test with a malformed file URI that passes validation but doesn't exist
        malformed_roots = [types.Root(uri="file:///invalid/malformed/path.pptx")]
        
        # Should not raise an exception, just skip invalid files
        set_client_roots(malformed_roots)
        
        session = get_session()
        assert session.loaded_presentation is None
        assert session.loaded_presentation_path is None
    
    def test_set_client_roots_nonexistent_file(self):
        """Test set_client_roots with nonexistent file paths."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions
        clear_session_store()
        
        # Test with file URI pointing to nonexistent file
        nonexistent_roots = [types.Root(uri="file:///nonexistent/file.pptx")]
        
        # Should not raise an exception, just skip nonexistent files
        set_client_roots(nonexistent_roots)
        
        session = get_session()
        assert session.loaded_presentation is None
        assert session.loaded_presentation_path is None


class TestEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_execute_python_code_with_complex_output(self):
        """Test execute_python_code with complex output including unicode and special characters."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.pptx', MagicMock()) as mock_pptx, \
             patch('mcp_server.server.tools.get_session') as mock_get_session:
            
            # Create a mock session with a loaded presentation
            mock_session = Mock()
            mock_presentation = Mock()
            mock_session.loaded_presentation = mock_presentation
            mock_get_session.return_value = mock_session
            
            # Execute code with unicode and special characters
            result = await execute_python_code("print('Hello 🌍 Unicode! \\n\\tTabbed text')")
            
            data = json.loads(result)
            assert data["success"] is True
            assert "Hello 🌍 Unicode!" in data["stdout"]
            assert "\tTabbed text" in data["stdout"]
    
    @pytest.mark.asyncio
    async def test_execute_python_code_with_imports(self):
        """Test execute_python_code with import statements."""
        from mcp_server.server.session import clear_session_store
        
        # Clear any existing sessions and set up a mock session
        clear_session_store()
        
        with patch('mcp_server.server.tools.pptx', MagicMock()) as mock_pptx, \
             patch('mcp_server.server.tools.get_session') as mock_get_session:
            
            # Create a mock session with a loaded presentation
            mock_session = Mock()
            mock_presentation = Mock()
            mock_session.loaded_presentation = mock_presentation
            mock_get_session.return_value = mock_session
            
            # Execute code with imports (should work with available modules)
            result = await execute_python_code("import json; print(json.dumps({'test': 'success'}))")
            
            data = json.loads(result)
            assert data["success"] is True
            assert '{"test": "success"}' in data["stdout"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])