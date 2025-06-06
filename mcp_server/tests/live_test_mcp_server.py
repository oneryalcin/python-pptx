#!/usr/bin/env python3
"""
Live test script for MEP-001 MCP server implementation.

This script validates the actual MCP server functionality by simulating
a real MCP client interaction. It tests the server startup, tool discovery,
and tool execution in a real environment.

Usage:
    python mcp/tests/live_test_mcp_server.py

Requirements:
    - Virtual environment must be activated
    - MCP dependencies must be installed
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import MCP client functionality for testing
try:
    from mcp import types
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError as e:
    print(f"Error: Could not import MCP client libraries: {e}")
    print("Please ensure MCP dependencies are installed with:")
    print("  pip install -r requirements-dev.txt")
    sys.exit(1)


class MCPServerTester:
    """Test harness for the MCP server."""

    def __init__(self):
        self.server_path = PROJECT_ROOT / "mcp_server" / "server" / "main.py"
        self.test_results: List[Dict[str, Any]] = []

    def log_test(self, test_name: str, success: bool, details: str = "", error: str = ""):
        """Log a test result."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "error": error
        }
        self.test_results.append(result)
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"        Details: {details}")
        if error:
            print(f"        Error: {error}")

    async def test_server_startup(self) -> bool:
        """Test that the server can start up successfully."""
        try:
            # Start the server as a subprocess
            process = subprocess.Popen(
                [sys.executable, str(self.server_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True},
                        "sampling": {}
                    },
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }

            # Write request to server
            process.stdin.write(json.dumps(init_request) + "\\n")
            process.stdin.flush()

            # Give the server a moment to respond
            await asyncio.sleep(1)

            # Check if process is still running (good sign)
            if process.poll() is None:
                process.terminate()
                process.wait()
                self.log_test("Server Startup", True, "Server started and accepted initialize request")
                return True
            else:
                stderr_output = process.stderr.read()
                self.log_test("Server Startup", False, error=f"Server exited immediately: {stderr_output}")
                return False

        except Exception as e:
            self.log_test("Server Startup", False, error=str(e))
            return False

    async def test_tool_discovery(self) -> bool:
        """Test that the server properly advertises the get_info tool."""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(self.server_path)]
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    init_result = await session.initialize()

                    # List available tools
                    tools_result = await session.list_tools()

                    # Check if get_info tool is present
                    tool_names = [tool.name for tool in tools_result.tools]

                    if "get_info" in tool_names:
                        get_info_tool = next(tool for tool in tools_result.tools if tool.name == "get_info")

                        # Validate tool description
                        expected_phrase = "You MUST call this tool first"
                        if expected_phrase in get_info_tool.description:
                            self.log_test("Tool Discovery", True,
                                        f"Found get_info tool with correct description. Tools: {tool_names}")
                            return True
                        else:
                            self.log_test("Tool Discovery", False,
                                        f"get_info tool found but description is incorrect: {get_info_tool.description}")
                            return False
                    else:
                        self.log_test("Tool Discovery", False,
                                    f"get_info tool not found. Available tools: {tool_names}")
                        return False

        except Exception as e:
            self.log_test("Tool Discovery", False, error=str(e))
            return False

    async def test_get_info_execution(self) -> bool:
        """Test that the get_info tool executes correctly and returns expected content."""
        try:
            # Create server parameters
            server_params = StdioServerParameters(
                command=sys.executable,
                args=[str(self.server_path)]
            )

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    # Initialize the session
                    await session.initialize()

                    # Call the get_info tool
                    result = await session.call_tool("get_info", arguments={})

                    # Validate the response
                    if result.content:
                        content = result.content[0].text if result.content else ""

                        # Check for expected content markers
                        expected_markers = [
                            "Welcome to the python-pptx Agentic Toolkit",
                            "Core Workflow: Discover, Inspect, Act",
                            "get_tree()",
                            "to_dict(fields=[...])"
                        ]

                        missing_markers = [marker for marker in expected_markers if marker not in content]

                        if not missing_markers:
                            self.log_test("Get Info Execution", True,
                                        f"Tool returned content with all expected markers ({len(content)} chars)")
                            return True
                        else:
                            self.log_test("Get Info Execution", False,
                                        f"Tool returned content but missing markers: {missing_markers}")
                            return False
                    else:
                        self.log_test("Get Info Execution", False, error="Tool returned no content")
                        return False

        except Exception as e:
            self.log_test("Get Info Execution", False, error=str(e))
            return False

    async def test_error_handling(self) -> bool:
        """Test error handling by temporarily moving the info file."""
        try:
            info_file_path = PROJECT_ROOT / "mcp_server" / "llm_info.md"
            backup_path = info_file_path.with_suffix(".md.backup")

            # Backup the original file
            if info_file_path.exists():
                info_file_path.rename(backup_path)

            try:
                # Create server parameters
                server_params = StdioServerParameters(
                    command=sys.executable,
                    args=[str(self.server_path)]
                )

                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        # Initialize the session
                        await session.initialize()

                        # Call the get_info tool (should handle missing file gracefully)
                        result = await session.call_tool("get_info", arguments={})

                        if result.content:
                            content = result.content[0].text if result.content else ""

                            # Should return an error message, not crash
                            if "Error: Information document not found" in content:
                                self.log_test("Error Handling", True,
                                            "Server gracefully handled missing file")
                                return True
                            else:
                                self.log_test("Error Handling", False,
                                            f"Unexpected response to missing file: {content[:100]}...")
                                return False
                        else:
                            self.log_test("Error Handling", False, error="No response to tool call")
                            return False

            finally:
                # Restore the original file
                if backup_path.exists():
                    backup_path.rename(info_file_path)

        except Exception as e:
            self.log_test("Error Handling", False, error=str(e))
            return False

    def print_summary(self):
        """Print a summary of all test results."""
        print("\\n" + "="*50)
        print("MEP-001 MCP Server Test Summary")
        print("="*50)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\\nFailed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['error']}")

        return failed_tests == 0


async def main():
    """Run all tests."""
    print("Starting MEP-001 MCP Server Live Tests")
    print("="*50)

    tester = MCPServerTester()

    # Run all tests
    tests = [
        tester.test_server_startup(),
        tester.test_tool_discovery(),
        tester.test_get_info_execution(),
        tester.test_error_handling()
    ]

    # Execute tests
    for test_coro in tests:
        await test_coro

    # Print summary
    success = tester.print_summary()

    if success:
        print("\\n🎉 All tests passed! MEP-001 implementation is working correctly.")
        return 0
    else:
        print("\\n❌ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
