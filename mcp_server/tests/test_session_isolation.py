#!/usr/bin/env python3
"""
Test session isolation to ensure multiple clients don't interfere with each other.

This test verifies that the session-based state management correctly isolates
presentation state between different client sessions.
"""

import asyncio
import threading
import time
from unittest.mock import Mock, patch
from pathlib import Path

import pytest
import sys

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.server.session import (
    get_session, set_client_roots, get_session_store, clear_session_store, SessionContext
)
from mcp_server.server.tools import execute_python_code, get_presentation_tree
from mcp import types


class TestSessionIsolation:
    """Test session isolation between multiple clients."""
    
    def setup_method(self):
        """Clear session store before each test."""
        clear_session_store()
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions_isolation(self):
        """Test that concurrent sessions maintain separate state."""
        
        # Mock pptx library
        with patch('mcp_server.server.session.pptx', Mock()):
            results = []
            errors = []
            
            def session_worker(session_id: str, should_load_presentation: bool):
                """Worker function to simulate a client session."""
                try:
                    # Force this thread to use a specific session ID
                    import mcp_server.server.session as session_module
                    session_module._current_session_id.value = session_id
                    
                    # Create session context
                    session = SessionContext(
                        session_id=session_id,
                        created_at=time.time(),
                        last_accessed=time.time(),
                        client_roots=[]
                    )
                    
                    if should_load_presentation:
                        # Mock a loaded presentation for this session
                        mock_presentation = Mock()
                        mock_presentation.slides = [f"slide_{session_id}"]
                        session.loaded_presentation = mock_presentation
                        session.loaded_presentation_path = Path(f"/test/{session_id}.pptx")
                    
                    # Store session
                    session_store = get_session_store()
                    session_store[session_id] = session
                    
                    # Get session and verify it's the right one
                    retrieved_session = get_session()
                    results.append({
                        'session_id': session_id,
                        'retrieved_session_id': retrieved_session.session_id,
                        'has_presentation': retrieved_session.loaded_presentation is not None,
                        'presentation_slides': getattr(retrieved_session.loaded_presentation, 'slides', None)
                    })
                    
                except Exception as e:
                    errors.append(f"Session {session_id}: {str(e)}")
            
            # Create multiple threads simulating different client sessions
            threads = []
            session_configs = [
                ("session_1", True),   # Has presentation
                ("session_2", False),  # No presentation
                ("session_3", True),   # Has presentation
            ]
            
            for session_id, should_load in session_configs:
                thread = threading.Thread(
                    target=session_worker, 
                    args=(session_id, should_load)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify no errors occurred
            assert not errors, f"Errors in session workers: {errors}"
            
            # Verify each session maintained its own state
            assert len(results) == 3
            
            # Check session 1 (has presentation)
            session_1_result = next(r for r in results if r['session_id'] == 'session_1')
            assert session_1_result['retrieved_session_id'] == 'session_1'
            assert session_1_result['has_presentation'] is True
            assert session_1_result['presentation_slides'] == ['slide_session_1']
            
            # Check session 2 (no presentation)
            session_2_result = next(r for r in results if r['session_id'] == 'session_2')
            assert session_2_result['retrieved_session_id'] == 'session_2'
            assert session_2_result['has_presentation'] is False
            assert session_2_result['presentation_slides'] is None
            
            # Check session 3 (has presentation)
            session_3_result = next(r for r in results if r['session_id'] == 'session_3')
            assert session_3_result['retrieved_session_id'] == 'session_3'
            assert session_3_result['has_presentation'] is True
            assert session_3_result['presentation_slides'] == ['slide_session_3']
    
    @pytest.mark.asyncio 
    async def test_session_cleanup(self):
        """Test that expired sessions are cleaned up."""
        
        # Create some test sessions
        old_time = time.time() - 7200  # 2 hours ago
        recent_time = time.time() - 60   # 1 minute ago
        
        old_session = SessionContext(
            session_id="old_session",
            created_at=old_time,
            last_accessed=old_time,
            client_roots=[]
        )
        
        recent_session = SessionContext(
            session_id="recent_session", 
            created_at=recent_time,
            last_accessed=recent_time,
            client_roots=[]
        )
        
        session_store = get_session_store()
        session_store["old_session"] = old_session
        session_store["recent_session"] = recent_session
        
        # Verify both sessions exist
        assert len(session_store) == 2
        
        # Import and call cleanup function with 1 hour max age
        from mcp_server.server.session import cleanup_expired_sessions
        cleanup_expired_sessions(max_age=3600)  # 1 hour
        
        # Verify old session was removed but recent session remains
        assert "old_session" not in session_store
        assert "recent_session" in session_store
        assert len(session_store) == 1
    
    @pytest.mark.asyncio
    async def test_tools_use_correct_session(self):
        """Test that tools access the correct session's data."""
        
        with patch('mcp_server.server.session.pptx', Mock()):
            # Create two sessions with different states
            session_1 = SessionContext(
                session_id="session_1",
                created_at=time.time(),
                last_accessed=time.time(),
                client_roots=[]
            )
            
            session_2 = SessionContext(
                session_id="session_2", 
                created_at=time.time(),
                last_accessed=time.time(),
                client_roots=[]
            )
            
            # Session 1 has a presentation, session 2 doesn't
            mock_presentation = Mock()
            mock_presentation.slides = ["slide1", "slide2"]
            session_1.loaded_presentation = mock_presentation
            session_1.loaded_presentation_path = Path("/test/session1.pptx")
            
            session_store = get_session_store()
            session_store["session_1"] = session_1
            session_store["session_2"] = session_2
            
            # Test session 1 can execute code
            with patch('mcp_server.server.tools.get_session', return_value=session_1):
                result = await execute_python_code("print('Hello from session 1')")
                import json
                result_data = json.loads(result)
                assert result_data["success"] is True
                assert "Hello from session 1" in result_data["stdout"]
            
            # Test session 2 cannot execute code (no presentation)
            with patch('mcp_server.server.tools.get_session', return_value=session_2):
                result = await execute_python_code("print('Hello from session 2')")
                result_data = json.loads(result)
                assert result_data["success"] is False
                assert "No PowerPoint presentation loaded" in result_data["error"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])