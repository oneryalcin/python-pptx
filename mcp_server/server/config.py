"""
Configuration settings for the MCP server.

Contains server constants, paths, and configuration values used throughout
the MCP server implementation.
"""

from pathlib import Path

# Server identification
SERVER_NAME = "pptx-agent-server"

# File paths
INFO_DOC_PATH = Path(__file__).parent.parent / "llm_info.md"

# Session management settings
DEFAULT_SESSION_MAX_AGE = 3600  # 1 hour in seconds

# Server capabilities and features
SERVER_DESCRIPTION = """
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