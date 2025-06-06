"""
MCP server for python-pptx agentic toolkit.

This server provides AI agents with access to python-pptx library capabilities
through the Model Context Protocol (MCP).
"""

import contextlib
import io
import json
import time
from pathlib import Path

from mcp.server import FastMCP

try:
    import pptx
except ImportError:
    pptx = None

# Initialize the FastMCP server
mcp = FastMCP("pptx-agent-server")

# Define the path to the info document
_INFO_DOC_PATH = Path(__file__).parent.parent / "llm_info.md"


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
async def execute_python_code(code: str, file_path: str) -> str:
    """
    Execute Python code with a loaded PowerPoint presentation available as 'prs'.
    
    Loads the specified PowerPoint file and executes the provided Python code
    with the presentation object available as 'prs' in the execution context.
    Captures stdout, stderr, and any exceptions during execution.
    
    Args:
        code: Python code to execute
        file_path: Path to PowerPoint file to load (.pptx)
        
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
    
    # Validate and sanitize file path
    try:
        file_path_obj = Path(file_path).resolve()
        
        # Basic security checks
        if not file_path_obj.exists():
            return json.dumps({
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": f"File not found: {file_path}",
                "execution_time": time.time() - start_time
            })
            
        if not file_path_obj.suffix.lower() == '.pptx':
            return json.dumps({
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": f"Invalid file type. Expected .pptx, got: {file_path_obj.suffix}",
                "execution_time": time.time() - start_time
            })
            
        # Check for path traversal attempts
        if '..' in str(file_path_obj):
            return json.dumps({
                "success": False,
                "stdout": "",
                "stderr": "",
                "error": "Invalid file path: path traversal not allowed",
                "execution_time": time.time() - start_time
            })
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": f"File path validation error: {str(e)}",
            "execution_time": time.time() - start_time
        })
    
    # Load presentation
    try:
        prs = pptx.Presentation(file_path_obj)
    except Exception as e:
        return json.dumps({
            "success": False,
            "stdout": "",
            "stderr": "",
            "error": f"Failed to load presentation: {str(e)}",
            "execution_time": time.time() - start_time
        })
    
    # Prepare execution context
    exec_globals = {
        "__builtins__": __builtins__,
        "prs": prs,
        "pptx": pptx,  # Make pptx module available too
        "Path": Path,   # Useful for file operations
        "print": print, # Ensure print works
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


if __name__ == "__main__":
    # Run the server using the stdio transport
    mcp.run(transport='stdio')
