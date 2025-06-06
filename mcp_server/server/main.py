"""
MCP server for python-pptx agentic toolkit.

This server provides AI agents with access to python-pptx library capabilities
through the Model Context Protocol (MCP). Implements MEP-004: Unified Save and Save As Tool.

Features:
- Automatic presentation loading from client roots
- Resource discovery and tree-based content reading
- Simplified execute_python_code tool (no file_path required)
- Unified save_presentation tool with security validation
- Session-based state management for multi-client support
"""

from mcp.server import FastMCP
from mcp import types

try:
    # Try relative imports first (when imported as module)
    from .config import SERVER_NAME
    from .session import set_client_roots
    from .tools import (
        get_info as get_info_impl, 
        execute_python_code as execute_python_code_impl, 
        save_presentation as save_presentation_impl, 
        get_presentation_tree as get_presentation_tree_impl
    )
except ImportError:
    # Fall back to absolute imports (when run as script)
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from mcp_server.server.config import SERVER_NAME
    from mcp_server.server.session import set_client_roots
    from mcp_server.server.tools import (
        get_info as get_info_impl, 
        execute_python_code as execute_python_code_impl, 
        save_presentation as save_presentation_impl, 
        get_presentation_tree as get_presentation_tree_impl
    )

# Initialize the FastMCP server
mcp = FastMCP(SERVER_NAME)


@mcp.tool()
async def get_info() -> str:
    """
    You MUST call this tool first before generating any Python code. It provides essential context and examples for interacting with the python-pptx library.
    """
    return await get_info_impl()


@mcp.tool()
async def execute_python_code(code: str) -> str:
    """
    Execute Python code with the currently loaded PowerPoint presentation available as 'prs'.
    """
    return await execute_python_code_impl(code)


@mcp.tool()
async def save_presentation(output_path: str = None) -> str:
    """
    Save the currently loaded PowerPoint presentation to disk. Supports both 'Save' and 'Save As' operations.
    """
    return await save_presentation_impl(output_path)


@mcp.resource("pptx://presentation")
async def get_presentation_tree() -> str:
    """Get the tree structure of the currently loaded PowerPoint presentation."""
    return await get_presentation_tree_impl()


# Register the roots handler to automatically load presentations
# Note: This functionality may need to be implemented differently based on MCP server capabilities
# For now, commenting out until we can research the proper approach
# @mcp.set_roots()
# async def handle_set_roots(roots: list[types.Root]) -> None:
#     """Handle client roots to automatically load presentations."""
#     set_client_roots(roots)


if __name__ == "__main__":
    # Run the server using the stdio transport
    mcp.run(transport='stdio')