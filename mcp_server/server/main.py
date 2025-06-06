"""
MCP server for python-pptx agentic toolkit.

This server provides AI agents with access to python-pptx library capabilities
through the Model Context Protocol (MCP).
"""

from pathlib import Path

from mcp.server import FastMCP

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


if __name__ == "__main__":
    # Run the server using the stdio transport
    mcp.run(transport='stdio')
