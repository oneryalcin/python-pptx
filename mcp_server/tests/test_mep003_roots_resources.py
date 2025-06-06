#!/usr/bin/env python3
"""
Unit tests for MEP-003: Root and Resource Management.

Tests the root handling, automatic presentation loading, and resource management
functionality introduced in MEP-003. This includes:
- Client root scanning and presentation auto-loading
- Resource discovery and tree-based content reading  
- Integration with MCP resource model
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import List

# Add the project root to Python path for imports
import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the server module
try:
    from mcp_server.server.main import (
        _set_client_roots, 
        _load_presentation,
        _loaded_presentation,
        _loaded_presentation_path,
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
        _set_client_roots([])
        
        # Should clear any loaded presentation
        assert _loaded_presentation is None
        assert _loaded_presentation_path is None
    
    @patch('mcp_server.server.main._load_presentation')
    def test_set_client_roots_with_pptx_file(self, mock_load_presentation):
        """Test setting roots with a .pptx file."""
        # Mock load_presentation to return success
        mock_load_presentation.return_value = True
        
        # Test with a direct .pptx file path
        with patch('mcp_server.server.main.urlparse') as mock_urlparse:
            with patch('mcp_server.server.main.Path') as mock_path_class:
                # Setup URL parsing
                mock_urlparse.return_value.scheme = 'file'
                mock_urlparse.return_value.path = '/test/presentation.pptx'
                
                # Setup path behavior
                mock_path = Mock()
                mock_path.exists.return_value = True
                mock_path.is_file.return_value = True
                mock_path.is_dir.return_value = False
                mock_path.suffix.lower.return_value = '.pptx'
                mock_path_class.return_value = mock_path
                
                roots = [types.Root(uri="file:///test/presentation.pptx")]
                _set_client_roots(roots)
                
                # Should call _load_presentation with the path
                mock_load_presentation.assert_called_once_with(mock_path)
    
    @patch('mcp_server.server.main._load_presentation')
    def test_set_client_roots_with_directory(self, mock_load_presentation):
        """Test setting roots with directory containing .pptx files."""
        # Mock load_presentation to return success
        mock_load_presentation.return_value = True
        
        # Test with a directory containing .pptx files
        with patch('mcp_server.server.main.urlparse') as mock_urlparse:
            with patch('mcp_server.server.main.Path') as mock_path_class:
                # Setup URL parsing
                mock_urlparse.return_value.scheme = 'file'
                mock_urlparse.return_value.path = '/test/dir'
                
                # Setup path behavior
                mock_dir_path = Mock()
                mock_file_path = Mock()
                
                mock_dir_path.exists.return_value = True
                mock_dir_path.is_file.return_value = False
                mock_dir_path.is_dir.return_value = True
                mock_dir_path.glob.return_value = [mock_file_path]
                
                mock_path_class.return_value = mock_dir_path
                
                roots = [types.Root(uri="file:///test/dir")]
                _set_client_roots(roots)
                
                # Should call _load_presentation with the found file
                mock_load_presentation.assert_called_once_with(mock_file_path)
    
    def test_load_presentation_success(self):
        """Test successful presentation loading."""
        with patch('mcp_server.server.main.pptx') as mock_pptx:
            mock_presentation = Mock()
            mock_pptx.Presentation.return_value = mock_presentation
            mock_pptx.is_not_none = True
            
            test_file = Path("/test/presentation.pptx")
            result = _load_presentation(test_file)
            
            assert result is True
            mock_pptx.Presentation.assert_called_once_with(test_file)
    
    def test_load_presentation_no_pptx_library(self):
        """Test presentation loading when pptx library is not available."""
        with patch('mcp_server.server.main.pptx', None):
            test_file = Path("/test/presentation.pptx")
            result = _load_presentation(test_file)
            
            assert result is False


class TestExecutePythonCodeTool:
    """Test the refactored execute_python_code tool."""
    
    @pytest.mark.asyncio
    async def test_execute_python_code_no_pptx_library(self):
        """Test execute_python_code when pptx library is not available."""
        with patch('mcp_server.server.main.pptx', None):
            result = await execute_python_code("print('test')")
            
            result_data = json.loads(result)
            assert result_data["success"] is False
            assert "python-pptx library is not available" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_execute_python_code_no_presentation_loaded(self):
        """Test execute_python_code when no presentation is loaded."""
        with patch('mcp_server.server.main.pptx', Mock()):
            with patch('mcp_server.server.main._loaded_presentation', None):
                result = await execute_python_code("print('test')")
                
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "No PowerPoint presentation loaded" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_execute_python_code_success(self):
        """Test successful Python code execution."""
        mock_presentation = Mock()
        
        with patch('mcp_server.server.main.pptx', Mock()):
            with patch('mcp_server.server.main._loaded_presentation', mock_presentation):
                result = await execute_python_code("print('Hello World')")
                
                result_data = json.loads(result)
                assert result_data["success"] is True
                assert "Hello World" in result_data["stdout"]
    
    @pytest.mark.asyncio
    async def test_execute_python_code_syntax_error(self):
        """Test Python code execution with syntax error."""
        mock_presentation = Mock()
        
        with patch('mcp_server.server.main.pptx', Mock()):
            with patch('mcp_server.server.main._loaded_presentation', mock_presentation):
                result = await execute_python_code("print('unclosed string")
                
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "Syntax error" in result_data["error"]
    
    @pytest.mark.asyncio
    async def test_execute_python_code_runtime_error(self):
        """Test Python code execution with runtime error."""
        mock_presentation = Mock()
        
        with patch('mcp_server.server.main.pptx', Mock()):
            with patch('mcp_server.server.main._loaded_presentation', mock_presentation):
                result = await execute_python_code("raise ValueError('test error')")
                
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "Runtime error" in result_data["error"]
                assert "test error" in result_data["error"]


class TestResourceHandlers:
    """Test resource functionality."""
    
    @pytest.mark.asyncio
    async def test_get_presentation_tree_no_presentation(self):
        """Test getting presentation tree when no presentation is loaded."""
        with patch('mcp_server.server.main._loaded_presentation', None):
            with patch('mcp_server.server.main._loaded_presentation_path', None):
                result = await get_presentation_tree()
                
                data = json.loads(result)
                assert "error" in data
                assert "No presentation loaded" in data["error"]
    
    @pytest.mark.asyncio
    async def test_get_presentation_tree_with_get_tree(self):
        """Test getting presentation tree when get_tree() is available."""
        mock_presentation = Mock()
        mock_presentation.get_tree.return_value = {"type": "presentation", "slides": []}
        test_path = Path("/test/presentation.pptx")
        
        with patch('mcp_server.server.main._loaded_presentation', mock_presentation):
            with patch('mcp_server.server.main._loaded_presentation_path', test_path):
                result = await get_presentation_tree()
                
                # Should return get_tree() output as JSON
                data = json.loads(result)
                assert data["type"] == "presentation"
                assert "slides" in data
    
    @pytest.mark.asyncio
    async def test_get_presentation_tree_without_get_tree(self):
        """Test getting presentation tree when get_tree() is not available."""
        mock_presentation = Mock()
        mock_presentation.slides = []  # Mock slides collection
        del mock_presentation.get_tree  # Remove get_tree method
        test_path = Path("/test/presentation.pptx")
        
        with patch('mcp_server.server.main._loaded_presentation', mock_presentation):
            with patch('mcp_server.server.main._loaded_presentation_path', test_path):
                result = await get_presentation_tree()
                
                # Should return fallback info
                data = json.loads(result)
                assert data["type"] == "presentation"
                assert data["slide_count"] == 0
                assert "get_tree() method not available" in data["note"]
    
    @pytest.mark.asyncio
    async def test_get_presentation_tree_error(self):
        """Test getting presentation tree when get_tree() raises an error."""
        mock_presentation = Mock()
        mock_presentation.get_tree.side_effect = RuntimeError("Tree generation failed")
        mock_presentation.slides = []
        test_path = Path("/test/presentation.pptx")
        
        with patch('mcp_server.server.main._loaded_presentation', mock_presentation):
            with patch('mcp_server.server.main._loaded_presentation_path', test_path):
                result = await get_presentation_tree()
                
                # Should return error info
                data = json.loads(result)
                assert data["type"] == "presentation"
                assert "Failed to get tree data" in data["error"]
                assert "Tree generation failed" in data["error"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])