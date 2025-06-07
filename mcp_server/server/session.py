"""
Session management for MCP server.

Handles client session state, presentation loading, and session lifecycle management.
Provides thread-safe session isolation for multi-client support.
"""

import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

from mcp import types

try:
    import pptx
except ImportError:
    pptx = None


@dataclass
class SessionContext:
    """Represents a client session with its state."""
    session_id: str
    created_at: float
    last_accessed: float
    client_roots: List[types.Root]
    loaded_presentation: Optional[pptx.Presentation] = None
    loaded_presentation_path: Optional[Path] = None
    
    def update_access(self):
        """Update the last accessed timestamp."""
        self.last_accessed = time.time()
    
    def load_presentation(self, file_path: Path) -> bool:
        """Load a presentation from the given file path."""
        if pptx is None:
            return False
            
        try:
            self.loaded_presentation = pptx.Presentation(file_path)
            self.loaded_presentation_path = file_path
            return True
        except Exception:
            self.loaded_presentation = None
            self.loaded_presentation_path = None
            return False


# Session management globals
_session_store: Dict[str, SessionContext] = {}
_session_lock = threading.Lock()
_current_session_id = threading.local()


def get_session_id() -> str:
    """
    Get the current session ID. Since FastMCP doesn't provide explicit session context,
    we use a thread-local approach. For now, we create a default session per thread.
    This is a temporary solution until we can implement proper session handling.
    """
    if not hasattr(_current_session_id, 'value'):
        # Create a new session for this thread
        session_id = str(uuid.uuid4())
        _current_session_id.value = session_id
        
        with _session_lock:
            if session_id not in _session_store:
                _session_store[session_id] = SessionContext(
                    session_id=session_id,
                    created_at=time.time(),
                    last_accessed=time.time(),
                    client_roots=[]
                )
    
    return _current_session_id.value


def get_session() -> SessionContext:
    """Get the current session context."""
    session_id = get_session_id()
    
    with _session_lock:
        session = _session_store.get(session_id)
        if session:
            session.update_access()
            return session
        else:
            # This shouldn't happen, but create a new session if needed
            session = SessionContext(
                session_id=session_id,
                created_at=time.time(),
                last_accessed=time.time(),
                client_roots=[]
            )
            _session_store[session_id] = session
            return session


def cleanup_expired_sessions(max_age: float = 3600) -> None:
    """Remove sessions that haven't been used for max_age seconds."""
    current_time = time.time()
    
    with _session_lock:
        expired_keys = [
            session_id for session_id, session in _session_store.items()
            if current_time - session.last_accessed > max_age
        ]
        
        for session_id in expired_keys:
            del _session_store[session_id]


def set_client_roots(roots: List[types.Root]) -> None:
    """Store the client-provided roots and attempt to load a presentation for the current session."""
    session = get_session()
    
    # Update session with new roots and clear any existing presentation
    session.client_roots = roots
    session.loaded_presentation = None
    session.loaded_presentation_path = None
    
    # Scan roots for .pptx files and load the first one found
    for root in roots:
        try:
            # Parse the root URI to get the file path
            parsed = urlparse(str(root.uri))
            if parsed.scheme == 'file':
                root_path = Path(parsed.path)
                if root_path.exists():
                    # Search for .pptx files in this root
                    if root_path.is_file() and root_path.suffix.lower() == '.pptx':
                        # Root points directly to a .pptx file
                        if session.load_presentation(root_path):
                            break
                    elif root_path.is_dir():
                        # Search directory for .pptx files
                        pptx_files = list(root_path.glob('*.pptx'))
                        if pptx_files:
                            if session.load_presentation(pptx_files[0]):
                                break
        except Exception:
            # Skip invalid roots
            continue


def load_presentation(file_path: Path) -> bool:
    """Load a presentation from the given file path for the current session."""
    session = get_session()
    return session.load_presentation(file_path)


# Export the session store for testing purposes
def get_session_store() -> Dict[str, SessionContext]:
    """Get the session store for testing purposes."""
    return _session_store


def clear_session_store() -> None:
    """Clear the session store for testing purposes."""
    global _session_store
    _session_store.clear()