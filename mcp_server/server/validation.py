"""
Path validation utilities for MCP server.

Provides security validation for file operations to ensure paths are within
client-configured root directories.
"""

from pathlib import Path
from urllib.parse import urlparse

from .session import get_session


def validate_output_path(output_path: Path) -> tuple[bool, str]:
    """
    Validate that the output path is within one of the client-provided roots.
    
    Args:
        output_path: The path to validate
        
    Returns:
        tuple[bool, str]: (is_valid, error_message_if_invalid)
    """
    session = get_session()
    
    if not session.client_roots:
        return False, "No client roots configured. Cannot save files."
    
    # Resolve the output path to handle relative paths and symlinks
    try:
        resolved_output = output_path.resolve()
    except (OSError, ValueError) as e:
        return False, f"Invalid output path: {str(e)}"
    
    # Check if the output path is within any of the client roots
    for root in session.client_roots:
        try:
            # Parse the root URI to get the file path
            parsed = urlparse(str(root.uri))
            if parsed.scheme == 'file':
                root_path = Path(parsed.path).resolve()
                
                # Check if the resolved output path is within this root
                try:
                    relative_path = resolved_output.relative_to(root_path)
                    return True, ""  # Path is valid - within this root
                except ValueError:
                    # Path is not within this root, continue checking other roots
                    continue
        except Exception:
            # Skip invalid roots
            continue
    
    return False, f"Output path '{output_path}' is not within any configured client root directory."