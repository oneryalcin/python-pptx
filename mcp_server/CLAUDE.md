# CLAUDE.md - MCP Server Development Guide

AI assistant guide for developing MCP (Model Context Protocol) servers for the python-pptx library.

## Quick Start

### Environment Setup
```bash
# Project has existing venv - ALWAYS activate first
source venv/bin/activate

# Install MCP dependencies
pip install -e .
pip install -r requirements-mcp.txt

# For development (includes MCP + dev tools)
pip install -r requirements-dev.txt

# Verify MCP installation
python -c "from mcp.server import FastMCP; print('MCP FastMCP available')"
```

**Critical:** ALL MCP development must use `source venv/bin/activate &&` prefix.

### Essential Commands
```bash
# Development cycle for MCP servers
python -m pytest mcp_server/tests/ -v && ruff check --fix mcp_server/ && ruff format mcp_server/

# Test server directly
python mcp_server/server/main.py

# Run comprehensive live tests
python mcp_server/tests/live_test_mcp_server.py

# Test with MCP Inspector (if available)
mcp install mcp_server/server/main.py
```

## MEP vs FEP Development Differences

### Key Distinctions

| Aspect | FEPs (Library Enhancement) | MEPs (MCP Server Enhancement) |
|--------|---------------------------|-------------------------------|
| **Focus** | Introspection capabilities (`to_dict`, `get_tree`) | Server tools and agent interaction |
| **Testing** | Unit tests + live scripts | Unit tests + MCP client tests + live scripts |
| **Dependencies** | Core python-pptx only | MCP framework + client libraries |
| **Import Issues** | Standard Python imports | **Critical:** Avoid naming conflicts with `mcp` package |
| **Architecture** | Library methods and classes | Server-client protocol implementation |
| **Validation** | Function calls and return values | Protocol compliance + tool execution |

### MEP-Specific Challenges

1. **Import Conflicts** 
   - ⚠️ **Never name directories `mcp/`** - conflicts with installed `mcp` package
   - Use descriptive names like `mcp_server/`, `pptx_mcp/`, etc.
   - Always test imports in clean Python sessions

2. **Protocol Compliance**
   - FastMCP handles most protocol details, but tool definitions must be precise
   - Tool descriptions become API documentation for AI agents
   - Async/await patterns are required for all tools

3. **Client-Server Testing**
   - Unit tests mock file I/O and tool logic
   - Live tests require actual MCP client-server communication
   - Transport-level testing (stdio) adds complexity

## Project Structure

```
mcp_server/                     # MCP server package (renamed to avoid conflicts)
├── server/                     # Server implementation
│   ├── __init__.py
│   └── main.py                 # FastMCP server with tools
├── tests/                      # Comprehensive test suite
│   ├── __init__.py
│   ├── test_server.py          # Unit tests (mocked)
│   └── live_test_mcp_server.py # End-to-end MCP protocol tests
├── llm_info.md                 # Static content for get_info tool
└── CLAUDE.md                   # This development guide
```

## MCP Development Patterns

### Server Implementation
```python
from mcp.server import FastMCP

# Initialize server
mcp = FastMCP("server-name")

# Define tools with proper async patterns
@mcp.tool()
async def tool_name(param: type) -> str:
    """
    Tool description becomes API documentation for AI agents.
    First line should be clear, imperative instruction.
    """
    try:
        # Tool implementation
        return result
    except Exception as e:
        return f"Error: {str(e)}"

# Run server
if __name__ == "__main__":
    mcp.run(transport='stdio')
```

### Key Patterns

1. **Tool Descriptions**
   - First line becomes the tool's primary description
   - Use imperative language ("Get", "Execute", "Create")
   - Include essential usage context for AI agents

2. **Error Handling**
   - Always return strings, even for errors
   - Provide user-friendly error messages
   - Include context about what went wrong

3. **Async Requirements**
   - All MCP tools must be `async def`
   - Use `await` for any I/O operations
   - Handle async context properly in tests

## Testing Strategy

### Three-Tier Testing Approach

#### 1. Unit Tests (`test_server.py`)
```python
@pytest.mark.asyncio
async def test_tool_functionality():
    """Test tool logic in isolation."""
    with patch("builtins.open", mock_open(read_data="test")):
        result = await tool_function()
        assert "expected" in result
```

**Focus:** Tool logic, error handling, edge cases
**Speed:** Fast (< 1 second)
**Scope:** Individual functions

#### 2. Live MCP Tests (`live_test_mcp_server.py`)
```python
async def test_mcp_protocol():
    """Test actual MCP client-server communication."""
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_path)]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("tool_name", arguments={})
            # Validate protocol compliance
```

**Focus:** Protocol compliance, client-server interaction
**Speed:** Medium (2-5 seconds)
**Scope:** Full server integration

#### 3. Manual Testing
```bash
# Direct server execution
python mcp_server/server/main.py

# MCP Inspector integration (if available)
mcp install mcp_server/server/main.py
```

**Focus:** Real-world usage, debugging
**Speed:** Interactive
**Scope:** End-to-end validation

### Testing Best Practices

1. **Always Test Protocol Compliance**
   - Verify server starts without errors
   - Check tool discovery works
   - Validate tool execution returns expected format

2. **Mock External Dependencies**
   - File system access
   - Network calls
   - Complex object creation

3. **Test Error Scenarios**
   - Missing files
   - Permission errors
   - Invalid inputs
   - Protocol violations

## Common Issues & Solutions

### Import Conflicts
```python
# ❌ Wrong - conflicts with mcp package
from mcp.server.main import tool

# ✅ Right - use project-specific path  
from mcp_server.server.main import tool
```

### Async Testing Issues
```python
# ❌ Wrong - missing asyncio
def test_async_function():
    result = async_function()  # Returns coroutine

# ✅ Right - proper async test
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
```

### Server Startup Problems
```bash
# Debug server startup
python mcp_server/server/main.py 2>&1 | head -20

# Check MCP package conflicts
python -c "import mcp.server; print('MCP OK')"
python -c "import mcp_server.server.main; print('Local OK')"
```

### Tool Description Issues
```python
# ❌ Wrong - generic description
@mcp.tool()
async def do_something() -> str:
    """Does something."""

# ✅ Right - specific, actionable description  
@mcp.tool()
async def get_presentation_info() -> str:
    """Get comprehensive information about the loaded PowerPoint presentation including slide count, themes, and structure."""
```

## MEP Development Workflow

### 1. Planning Phase
- Define tool purpose and AI agent use case
- Specify input/output formats
- Identify integration points with python-pptx library
- Plan error handling strategies

### 2. Implementation Phase
```bash
# Create new branch
git checkout -b mep-XXX-tool-name

# Implement server changes
# 1. Add tool to main.py
# 2. Create comprehensive tests
# 3. Update documentation

# Test thoroughly
python -m pytest mcp_server/tests/ -v
python mcp_server/tests/live_test_mcp_server.py
```

### 3. Validation Phase
- Unit tests: 100% pass rate required
- Live tests: Full MCP protocol compliance
- Manual testing: Real client interaction
- Error scenario testing: Graceful degradation

### 4. Documentation Phase
- Update tool descriptions for AI clarity
- Document any new patterns or learnings
- Update ROADMAP_MEP.md progress
- Include test results in PR

## Debugging Guide

### Server Won't Start
```bash
# Check for import conflicts
python -c "import mcp_server.server.main"

# Check MCP installation
python -c "from mcp.server import FastMCP"

# Debug step by step
python -c "
from mcp.server import FastMCP
server = FastMCP('test')
print('Server created successfully')
"
```

### Tool Not Found
```bash
# Check tool registration
python -c "
from mcp_server.server.main import mcp
print([tool.name for tool in mcp.list_tools()])
"
```

### Client Connection Issues
```bash
# Test basic protocol
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | python mcp_server/server/main.py
```

### Performance Issues
```python
# Add timing to tools
import time

@mcp.tool()
async def slow_tool() -> str:
    start = time.time()
    # ... tool logic ...
    duration = time.time() - start
    return f"Result (took {duration:.2f}s)"
```

## Dependencies & Package Management

### Core MCP Dependencies
```
mcp[cli]              # Official MCP SDK with CLI tools
httpx                 # HTTP client for async operations  
python-dotenv         # Environment variable management
```

### Development Dependencies
```
pytest-asyncio        # Async test support
pytest                # Core testing framework
```

### Dependency Management
- Add new dependencies to `requirements-dev.txt`
- Use specific versions for stability
- Test installation in clean environments
- Document any platform-specific requirements

## Security Considerations

### Input Validation
```python
@mcp.tool()
async def secure_tool(user_input: str) -> str:
    # Validate inputs
    if not user_input or len(user_input) > 1000:
        return "Error: Invalid input length"
    
    # Sanitize file paths
    if ".." in user_input or user_input.startswith("/"):
        return "Error: Invalid path"
```

### File System Access
- Restrict to project directory
- Validate all file paths
- Handle permission errors gracefully
- Never expose system files

### Error Information
- Don't leak sensitive paths in error messages
- Sanitize stack traces
- Provide helpful but safe error context

---

## MCP Documentation Resources

### Local Documentation
- **`mcp-llm-annotated.txt`** - Fast lookup guide for MCP concepts with line-based indexing
- **`mcp-llm.txt`** - Complete MCP documentation (19k+ lines) - DO NOT load fully into context

**Usage Example:**
```bash
# Find tools implementation guidance
# Check mcp-llm-annotated.txt → "Tools Overview & Implementation: Lines 2270-2750"
# Then: Read file_path="mcp_server/mcp-llm.txt" offset=2270 limit=480
```

### Official Python SDK Resources
- **Repository:** https://github.com/modelcontextprotocol/python-sdk
- **Examples:** https://github.com/modelcontextprotocol/python-sdk/tree/main/examples
- **Core patterns, server implementations, and client usage examples**

### Quick MCP Concepts Reference
- **Tools:** Lines 2270-2750 (implementation patterns, security)
- **Resources:** Lines 1680-1939 (file access, content discovery)  
- **Prompts:** Lines 1251-1679 (dynamic content generation)
- **Client Development:** Lines 3950-5585 (integration guide)
- **Server Development:** Lines 5586-7380 (comprehensive server guide)
- **Debugging:** Lines 3182-3627 (troubleshooting, inspector tools)

---

## Status Summary

This guide covers the essential patterns for MEP development based on MEP-001 implementation. Key learnings:

1. **Import Management:** Critical to avoid `mcp` package conflicts
2. **Protocol Testing:** Live tests essential for MCP compliance  
3. **Error Handling:** Must be comprehensive and user-friendly
4. **Tool Design:** Descriptions become API docs for AI agents

Future MEPs should follow these patterns and update this guide with new learnings.