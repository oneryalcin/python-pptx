"""
MCP server for python-pptx agentic toolkit.

This server provides AI agents with access to python-pptx library capabilities
through the Model Context Protocol (MCP). Implements MEP-003: Root and Resource Management.

Features:
- Automatic presentation loading from client roots
- Resource discovery and tree-based content reading
- Simplified execute_python_code tool (no file_path required)
"""

import contextlib
import io
import json
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from mcp.server import FastMCP
from mcp import types

try:
    import pptx
except ImportError:
    pptx = None

# Initialize the FastMCP server
mcp = FastMCP("pptx-agent-server")

# Define the path to the info document
_INFO_DOC_PATH = Path(__file__).parent.parent / "llm_info.md"

# Global state for root management and loaded presentation
_client_roots: List[types.Root] = []
_loaded_presentation: Optional[pptx.Presentation] = None
_loaded_presentation_path: Optional[Path] = None


def _set_client_roots(roots: List[types.Root]) -> None:
    """Store the client-provided roots and attempt to load a presentation."""
    global _client_roots, _loaded_presentation, _loaded_presentation_path
    
    _client_roots = roots
    _loaded_presentation = None
    _loaded_presentation_path = None
    
    # Scan roots for .pptx files and load the first one found
    for root in roots:
        try:
            # Parse the root URI to get the file path
            parsed = urlparse(root.uri)
            if parsed.scheme == 'file':
                root_path = Path(parsed.path)
                if root_path.exists():
                    # Search for .pptx files in this root
                    if root_path.is_file() and root_path.suffix.lower() == '.pptx':
                        # Root points directly to a .pptx file
                        _load_presentation(root_path)
                        break
                    elif root_path.is_dir():
                        # Search directory for .pptx files
                        pptx_files = list(root_path.glob('*.pptx'))
                        if pptx_files:
                            _load_presentation(pptx_files[0])
                            break
        except Exception:
            # Skip invalid roots
            continue


def _load_presentation(file_path: Path) -> bool:
    """Load a presentation from the given file path."""
    global _loaded_presentation, _loaded_presentation_path
    
    if pptx is None:
        return False
        
    try:
        _loaded_presentation = pptx.Presentation(file_path)
        _loaded_presentation_path = file_path
        return True
    except Exception:
        _loaded_presentation = None
        _loaded_presentation_path = None
        return False


@mcp.tool()
async def get_info() -> str:
    """
    You MUST call this tool first before generating any Python code. It provides essential context and examples for interacting with the python-pptx library.
    
    This tool provides the essential "onboarding manual" for AI agents working with
    the python-pptx library. It explains the two-phase workflow (discover, inspect, act)
    and provides concrete code examples.
    
    Returns:
        str: Markdown content with instructions and examples
    """
    try:
        with open(_INFO_DOC_PATH, encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return "# Error: Information document is empty."

        return content

    except FileNotFoundError:
        return f"# Error: Information document not found at {_INFO_DOC_PATH}"
    except PermissionError:
        return "# Error: Permission denied reading information document."
    except UnicodeDecodeError:
        return "# Error: Could not decode information document (encoding issue)."
    except Exception as e:
        return f"# Error: Could not read information document.\n\n{str(e)}"


@mcp.tool()
async def execute_python_code(code: str) -> str:
    """
    Execute Python code with the currently loaded PowerPoint presentation available as 'prs'.
    
    The presentation is automatically loaded from the client-provided roots. The loaded
    presentation object is available as 'prs' in the execution context.
    Captures stdout, stderr, and any exceptions during execution.
    
    Args:
        code: Python code to execute
        
    Returns:
        JSON string with execution results including stdout, stderr, and any errors
    """
    start_time = time.time()
    
    # Validate python-pptx is available
    if pptx is None:
        return json.dumps({
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": "python-pptx library is not available",
            "execution_time": time.time() - start_time
        })
    
    # Check if a presentation is loaded
    if _loaded_presentation is None:
        return json.dumps({
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": "No PowerPoint presentation loaded. Ensure a .pptx file is available in the client roots.",
            "execution_time": time.time() - start_time
        })
    
    # Use the pre-loaded presentation
    prs = _loaded_presentation
    
    # Prepare execution context
    exec_globals = {
        "__builtins__": __builtins__,
        "prs": prs,
        "pptx": pptx,  # Make pptx module available too
        "Path": Path,   # Useful for file operations
        "print": print, # Ensure print works
        "json": json,   # Make json available for output formatting
    }
    
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        with contextlib.redirect_stdout(stdout_capture), \
             contextlib.redirect_stderr(stderr_capture):
            # Execute the provided code
            exec(code, exec_globals)
            
        return json.dumps({
            "success": True,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "error": None,
            "execution_time": time.time() - start_time
        })
        
    except SyntaxError as e:
        return json.dumps({
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "error": f"Syntax error in Python code: {str(e)}",
            "execution_time": time.time() - start_time
        })
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue(),
            "error": f"Runtime error: {str(e)}",
            "execution_time": time.time() - start_time
        })


@mcp.resource("pptx://presentation")
async def get_presentation_tree() -> str:
    """Get the tree structure of the currently loaded PowerPoint presentation."""
    if _loaded_presentation is None or _loaded_presentation_path is None:
        return json.dumps({
            "error": "No presentation loaded",
            "message": "Ensure a .pptx file is available in the client roots."
        }, indent=2)
    
    # Return get_tree() output if available, otherwise return basic info
    try:
        if hasattr(_loaded_presentation, 'get_tree'):
            tree_data = _loaded_presentation.get_tree()
            return json.dumps(tree_data, indent=2)
        else:
            # Fallback: basic presentation info
            info = {
                "type": "presentation",
                "slide_count": len(_loaded_presentation.slides),
                "file_path": str(_loaded_presentation_path),
                "note": "get_tree() method not available. Please ensure you have the latest python-pptx with introspection features."
            }
            return json.dumps(info, indent=2)
    except Exception as e:
        # If get_tree() fails, return error info
        error_info = {
            "type": "presentation", 
            "slide_count": len(_loaded_presentation.slides),
            "file_path": str(_loaded_presentation_path),
            "error": f"Failed to get tree data: {str(e)}"
        }
        return json.dumps(error_info, indent=2)


if __name__ == "__main__":
    # Run the server using the stdio transport
    mcp.run(transport='stdio')
