"""
MCP tool implementations for python-pptx agentic toolkit.

Contains all @mcp.tool() and @mcp.resource() implementations for the server.
Each tool provides specific functionality for AI agents to interact with PowerPoint presentations.
"""

import contextlib
import io
import json
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import pptx
except ImportError:
    pptx = None

from .config import INFO_DOC_PATH
from .session import cleanup_expired_sessions, get_session
from .validation import validate_output_path


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
        with open(INFO_DOC_PATH, encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return "# Error: Information document is empty."

        return content

    except FileNotFoundError:
        return f"# Error: Information document not found at {INFO_DOC_PATH}"
    except PermissionError:
        return "# Error: Permission denied reading information document."
    except UnicodeDecodeError:
        return "# Error: Could not decode information document (encoding issue)."
    except Exception as e:
        return f"# Error: Could not read information document.\n\n{str(e)}"


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

    # Clean up expired sessions periodically
    cleanup_expired_sessions()

    # Get the current session
    session = get_session()

    # Validate python-pptx is available
    if pptx is None:
        return json.dumps({
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": "python-pptx library is not available",
            "execution_time": time.time() - start_time
        })

    # Check if a presentation is loaded in this session
    if session.loaded_presentation is None:
        return json.dumps({
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": "No PowerPoint presentation loaded. Ensure a .pptx file is available in the client roots.",
            "execution_time": time.time() - start_time
        })

    # Use the session's pre-loaded presentation
    prs = session.loaded_presentation

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


async def save_presentation(output_path: Optional[str] = None) -> str:
    """
    Save the currently loaded PowerPoint presentation to disk. Supports both 'Save' and 'Save As' operations.
    
    If output_path is None, overwrites the original file (Save operation).
    If output_path is provided, saves to the new location (Save As operation).
    All output paths must be within the client-configured root directories for security.
    
    IMPORTANT: The parent directory of the output path must already exist. This tool will not create directories.
    
    Args:
        output_path: Optional path where to save the presentation. If None, saves to original location.
                    The parent directory must exist.
        
    Returns:
        JSON string with save operation results including success status and file path
    """
    start_time = time.time()

    # Clean up expired sessions periodically
    cleanup_expired_sessions()

    # Get the current session
    session = get_session()

    # Validate python-pptx is available
    if pptx is None:
        return json.dumps({
            "success": False,
            "operation": "save",
            "file_path": None,
            "error": "python-pptx library is not available",
            "execution_time": time.time() - start_time
        })

    # Check if a presentation is loaded in this session
    if session.loaded_presentation is None:
        return json.dumps({
            "success": False,
            "operation": "save",
            "file_path": None,
            "error": "No PowerPoint presentation loaded. Ensure a .pptx file is available in the client roots.",
            "execution_time": time.time() - start_time
        })

    # Determine the target file path
    if output_path is None:
        # Save operation: use the original file path
        if session.loaded_presentation_path is None:
            return json.dumps({
                "success": False,
                "operation": "save",
                "file_path": None,
                "error": "Cannot determine original file path for save operation.",
                "execution_time": time.time() - start_time
            })
        target_path = session.loaded_presentation_path
        operation = "save"
    else:
        # Save As operation: use the provided output path
        target_path = Path(output_path)
        operation = "save_as"

    # Validate the target path is within client roots
    is_valid, validation_error = validate_output_path(target_path)
    if not is_valid:
        return json.dumps({
            "success": False,
            "operation": operation,
            "file_path": str(target_path),
            "error": f"Security validation failed: {validation_error}",
            "execution_time": time.time() - start_time
        })

    # Validate that the target directory exists (no automatic creation per specification)
    if not target_path.parent.exists():
        return json.dumps({
            "success": False,
            "operation": operation,
            "file_path": str(target_path),
            "error": f"Parent directory does not exist: {target_path.parent}. Please ensure the directory exists before saving.",
            "execution_time": time.time() - start_time
        })

    # Attempt to save the presentation
    try:
        session.loaded_presentation.save(str(target_path))

        # Update session state if this was a Save As operation
        if operation == "save_as":
            session.loaded_presentation_path = target_path

        return json.dumps({
            "success": True,
            "operation": operation,
            "file_path": str(target_path),
            "error": None,
            "execution_time": time.time() - start_time
        })

    except PermissionError:
        return json.dumps({
            "success": False,
            "operation": operation,
            "file_path": str(target_path),
            "error": "Permission denied: Cannot write to target file. Check file permissions and ensure the file is not open in another application.",
            "execution_time": time.time() - start_time
        })

    except Exception as e:
        return json.dumps({
            "success": False,
            "operation": operation,
            "file_path": str(target_path),
            "error": f"Failed to save presentation: {str(e)}",
            "execution_time": time.time() - start_time
        })


async def get_presentation_tree() -> str:
    """Get the tree structure of the currently loaded PowerPoint presentation."""
    # Clean up expired sessions periodically
    cleanup_expired_sessions()

    # Get the current session
    session = get_session()

    if session.loaded_presentation is None or session.loaded_presentation_path is None:
        return json.dumps({
            "error": "No presentation loaded",
            "message": "Ensure a .pptx file is available in the client roots.",
            "session_id": session.session_id  # Include session ID for debugging
        }, indent=2)

    # Return get_tree() output if available, otherwise return basic info
    try:
        if hasattr(session.loaded_presentation, 'get_tree'):
            tree_data = session.loaded_presentation.get_tree()
            return json.dumps(tree_data, indent=2)
        else:
            # Fallback: basic presentation info
            info = {
                "type": "presentation",
                "slide_count": len(session.loaded_presentation.slides),
                "file_path": str(session.loaded_presentation_path),
                "session_id": session.session_id,
                "note": "get_tree() method not available. Please ensure you have the latest python-pptx with introspection features."
            }
            return json.dumps(info, indent=2)
    except Exception as e:
        # If get_tree() fails, return error info
        error_info = {
            "type": "presentation",
            "slide_count": len(session.loaded_presentation.slides),
            "file_path": str(session.loaded_presentation_path),
            "session_id": session.session_id,
            "error": f"Failed to get tree data: {str(e)}"
        }
        return json.dumps(error_info, indent=2)


async def provide_feedback(feedback_text: str, is_success: bool, missing_capability: Optional[str] = None) -> str:
    """
    Provide structured feedback about the success or failure of tasks, helping improve the system over time.
    
    This tool enables the "Learn" phase of the agentic workflow. AI agents should use this tool to report
    task outcomes, challenges encountered, and missing capabilities in python-pptx.
    
    Args:
        feedback_text: Detailed description of what happened, what worked, or what failed
        is_success: True if the task completed successfully, False if it failed or encountered issues
        missing_capability: Optional description of any missing python-pptx functionality that would have helped
        
    Returns:
        JSON string confirming feedback receipt
    """
    # Construct structured log message per MEP-006 specification
    missing_str = missing_capability if missing_capability is not None else "None"
    log_message = f"[AGENT_FEEDBACK] | SUCCESS: {is_success} | MISSING: {missing_str} | TEXT: \"{feedback_text}\""

    # Log to stderr for developer review
    print(log_message, file=sys.stderr, flush=True)

    # Return confirmation message
    return json.dumps({
        "status": "Feedback received. Thank you."
    })
