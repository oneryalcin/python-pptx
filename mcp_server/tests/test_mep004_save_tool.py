"""
Unit tests for MEP-004: Unified Save and Save As Tool.

Tests the save_presentation tool and related path validation functionality.
Uses mocked file operations for isolated testing.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from urllib.parse import urlparse

from mcp import types

# Import the server functions to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from main import (
    save_presentation,
    _validate_output_path,
    _get_session,
    _set_client_roots,
    SessionContext
)


@pytest.fixture
def mock_session():
    """Create a mock session with default setup."""
    with patch('main._get_session') as mock_get_session:
        # Create a mock presentation object
        mock_prs = MagicMock()
        mock_prs.save = MagicMock()
        
        # Create session context
        session = SessionContext(
            session_id="test-session",
            created_at=1234567890.0,
            last_accessed=1234567890.0,
            client_roots=[
                types.Root(uri="file:///test/root", name="test_root")
            ],
            loaded_presentation=mock_prs,
            loaded_presentation_path=Path("/test/root/presentation.pptx")
        )
        
        mock_get_session.return_value = session
        yield session


@pytest.fixture
def mock_no_session():
    """Create a mock session with no presentation loaded."""
    with patch('main._get_session') as mock_get_session:
        session = SessionContext(
            session_id="test-session",
            created_at=1234567890.0,
            last_accessed=1234567890.0,
            client_roots=[
                types.Root(uri="file:///test/root", name="test_root")
            ],
            loaded_presentation=None,
            loaded_presentation_path=None
        )
        
        mock_get_session.return_value = session
        yield session


class TestPathValidation:
    """Test the _validate_output_path function."""
    
    def test_validate_output_path_within_root(self, mock_session):
        """Test path validation for valid path within root.""" 
        # Create test paths that exist in the filesystem for this test
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir).resolve()  # Resolve to handle symlinks (like /var -> /private/var on macOS)
            output_path = temp_path / "subfolder" / "output.pptx"
            
            # Update session to use the resolved temp directory
            mock_session.client_roots = [
                types.Root(uri=f"file://{temp_path}", name="test_root")
            ]
            
            is_valid, error = _validate_output_path(output_path)
            
            assert is_valid is True
            assert error == ""
    
    def test_validate_output_path_outside_root(self, mock_session):
        """Test path validation for path outside root."""
        output_path = Path("/outside/root/output.pptx")
        
        # Mock Path.resolve for all path instances
        def mock_resolve(self):
            return self
            
        with patch.object(Path, 'resolve', mock_resolve):
            is_valid, error = _validate_output_path(output_path)
            
            assert is_valid is False
            assert "not within any configured client root" in error
    
    def test_validate_output_path_no_roots(self):
        """Test path validation when no client roots are configured."""
        with patch('main._get_session') as mock_get_session:
            session = SessionContext(
                session_id="test-session",
                created_at=1234567890.0,
                last_accessed=1234567890.0,
                client_roots=[],  # No roots
                loaded_presentation=None,
                loaded_presentation_path=None
            )
            mock_get_session.return_value = session
            
            output_path = Path("/test/output.pptx")
            is_valid, error = _validate_output_path(output_path)
            
            assert is_valid is False
            assert "No client roots configured" in error
    
    def test_validate_output_path_invalid_path(self, mock_session):
        """Test path validation for invalid path."""
        output_path = Path("/test/root/output.pptx")
        
        def mock_resolve_error(self):
            raise OSError("Invalid path")
            
        with patch.object(Path, 'resolve', mock_resolve_error):
            is_valid, error = _validate_output_path(output_path)
            
            assert is_valid is False
            assert "Invalid output path" in error


class TestSavePresentationTool:
    """Test the save_presentation tool."""
    
    @pytest.mark.asyncio
    async def test_save_presentation_no_pptx(self):
        """Test save_presentation when python-pptx is not available."""
        with patch('main.pptx', None):
            result = await save_presentation()
            
            data = json.loads(result)
            assert data["success"] is False
            assert "python-pptx library is not available" in data["error"]
    
    @pytest.mark.asyncio
    async def test_save_presentation_no_loaded_presentation(self, mock_no_session):
        """Test save_presentation when no presentation is loaded."""
        with patch('main.pptx', MagicMock()):
            result = await save_presentation()
            
            data = json.loads(result)
            assert data["success"] is False
            assert "No PowerPoint presentation loaded" in data["error"]
    
    @pytest.mark.asyncio
    async def test_save_presentation_success_original_path(self, mock_session):
        """Test successful save to original path (Save operation)."""
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(True, "")), \
             patch('main._cleanup_expired_sessions'), \
             patch('pathlib.Path.mkdir'):
            
            result = await save_presentation()
            
            data = json.loads(result)
            assert data["success"] is True
            assert data["operation"] == "save"
            assert data["file_path"] == "/test/root/presentation.pptx"
            assert data["error"] is None
            
            # Verify the presentation was saved
            mock_session.loaded_presentation.save.assert_called_once_with("/test/root/presentation.pptx")
    
    @pytest.mark.asyncio
    async def test_save_presentation_success_new_path(self, mock_session):
        """Test successful save to new path (Save As operation)."""
        output_path = "/test/root/new_presentation.pptx"
        
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(True, "")), \
             patch('main._cleanup_expired_sessions'), \
             patch.object(Path, 'parent') as mock_parent, \
             patch.object(Path, 'mkdir'):
            
            # Mock the parent.mkdir call
            mock_parent.mkdir = MagicMock()
            
            result = await save_presentation(output_path)
            
            data = json.loads(result)
            assert data["success"] is True
            assert data["operation"] == "save_as"
            assert data["file_path"] == output_path
            assert data["error"] is None
            
            # Verify the presentation was saved to new path
            mock_session.loaded_presentation.save.assert_called_once_with(output_path)
            
            # Verify session state was updated
            assert str(mock_session.loaded_presentation_path) == output_path
    
    @pytest.mark.asyncio
    async def test_save_presentation_path_validation_failed(self, mock_session):
        """Test save_presentation when path validation fails."""
        output_path = "/outside/root/output.pptx"
        
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(False, "Path outside root")), \
             patch('main._cleanup_expired_sessions'):
            
            result = await save_presentation(output_path)
            
            data = json.loads(result)
            assert data["success"] is False
            assert data["operation"] == "save_as"
            assert "Security validation failed" in data["error"]
            assert "Path outside root" in data["error"]
    
    @pytest.mark.asyncio
    async def test_save_presentation_permission_error(self, mock_session):
        """Test save_presentation when permission error occurs."""
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(True, "")), \
             patch('main._cleanup_expired_sessions'), \
             patch.object(Path, 'parent') as mock_parent:
            
            # Mock the parent.mkdir call
            mock_parent.mkdir = MagicMock()
            
            # Mock save to raise PermissionError
            mock_session.loaded_presentation.save.side_effect = PermissionError("Access denied")
            
            result = await save_presentation()
            
            data = json.loads(result)
            assert data["success"] is False
            assert data["operation"] == "save"
            assert "Permission denied" in data["error"]
    
    @pytest.mark.asyncio
    async def test_save_presentation_general_error(self, mock_session):
        """Test save_presentation when general error occurs during save."""
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(True, "")), \
             patch('main._cleanup_expired_sessions'), \
             patch.object(Path, 'parent') as mock_parent:
            
            # Mock the parent.mkdir call
            mock_parent.mkdir = MagicMock()
            
            # Mock save to raise general exception
            mock_session.loaded_presentation.save.side_effect = Exception("Disk full")
            
            result = await save_presentation()
            
            data = json.loads(result)
            assert data["success"] is False
            assert data["operation"] == "save"
            assert "Failed to save presentation" in data["error"]
            assert "Disk full" in data["error"]
    
    @pytest.mark.asyncio
    async def test_save_presentation_directory_creation_error(self, mock_session):
        """Test save_presentation when directory creation fails."""
        output_path = "/test/root/new/folder/output.pptx"
        
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(True, "")), \
             patch('main._cleanup_expired_sessions'), \
             patch.object(Path, 'parent') as mock_parent:
            
            # Mock mkdir to raise exception
            mock_parent.mkdir.side_effect = OSError("Cannot create directory")
            
            result = await save_presentation(output_path)
            
            data = json.loads(result)
            assert data["success"] is False
            assert data["operation"] == "save_as"
            assert "Failed to create target directory" in data["error"]
    
    @pytest.mark.asyncio
    async def test_save_presentation_no_original_path(self):
        """Test save_presentation when no original path is available for Save operation."""
        with patch('main._get_session') as mock_get_session, \
             patch('main.pptx', MagicMock()), \
             patch('main._cleanup_expired_sessions'):
            
            # Create session with presentation but no path
            session = SessionContext(
                session_id="test-session",
                created_at=1234567890.0,
                last_accessed=1234567890.0,
                client_roots=[types.Root(uri="file:///test/root", name="test_root")],
                loaded_presentation=MagicMock(),
                loaded_presentation_path=None  # No original path
            )
            mock_get_session.return_value = session
            
            result = await save_presentation()
            
            data = json.loads(result)
            assert data["success"] is False
            assert data["operation"] == "save"
            assert "Cannot determine original file path" in data["error"]


class TestExecutionTime:
    """Test that save operations include execution time."""
    
    @pytest.mark.asyncio
    async def test_save_presentation_includes_execution_time(self, mock_session):
        """Test that save_presentation includes execution_time in response."""
        with patch('main.pptx', MagicMock()), \
             patch('main._validate_output_path', return_value=(True, "")), \
             patch('main._cleanup_expired_sessions'), \
             patch.object(Path, 'parent') as mock_parent:
            
            # Mock the parent.mkdir call
            mock_parent.mkdir = MagicMock()
            
            result = await save_presentation()
            
            data = json.loads(result)
            assert "execution_time" in data
            assert isinstance(data["execution_time"], (int, float))
            assert data["execution_time"] >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])