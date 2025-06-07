While the `python-pptx` FEPs focus on *exposing* the data, the MCP server is what *packages and presents* that data to the AI agent. A well-designed server is just as critical as a well-designed introspection API.

Let's create a parallel roadmap for building our `python-pptx` MCP server, which we'll call **MEPs (MCP Enhancement Proposals)**. We'll use the same principles of iterative development and clear, focused goals.

---

### **Definitive MEP Roadmap for the `pptx-agent-server` (Final Version)**

**Project Vision:** To create a robust, secure, and intelligent MCP server that acts as the definitive bridge between an AI agent and the `python-pptx` library, enabling the agent to safely and effectively analyze, modify, and create PowerPoint presentations.

**Guiding Principles:**
1.  **User-Controlled vs. Model-Controlled:** Clearly distinguish between features the user must explicitly invoke (`Prompts`) and features the model can use autonomously (`Tools`).
2.  **Security First:** Operate on a "least privilege" basis, especially concerning file system access.
3.  **Agent-Centric Design:** Design tools to support the "See -> Understand -> Act -> Learn" agentic workflow.

---

#### **Tier 1: Core Functionality (The Foundation)**

These MEPs establish the basic server and its primary interaction tools.

*   **MEP-001: Server Bootstrap & `get_info` Tool** ✅ **COMPLETED**
    *   **Goal:** Create the basic Python MCP server structure and implement the mandatory "onboarding manual" tool.
    *   **Implementation Notes:**
        1.  ✅ Set up MCP server using official `mcp[cli]` package with FastMCP framework.
        2.  ✅ Implemented server with proper FastMCP initialization and stdio transport.
        3.  ✅ Created the **`get_info()` tool** with comprehensive error handling.
        4.  ✅ Created static markdown document with corrected code examples for the two-phase workflow.
        5.  ✅ Directory structure: `mcp_server/` (renamed to avoid import conflicts).
    *   **MCP Concepts Used:** Tools, FastMCP Server, stdio transport.
    *   **Test Results:** 10/10 unit tests passing, 4/4 live tests passing (100% success rate).
    *   **Priority:** **CRITICAL.** This is the entry point for any agent interaction.

*   **MEP-002: The `execute_python_code` Tool** ✅ **COMPLETED**
    *   **Goal:** Create the primary "Act" tool that allows the agent to run `python-pptx` code.
    *   **Implementation Notes:**
        1.  ✅ Implemented the **`execute_python_code(code: str, file_path: str)` tool**.
        2.  ✅ Tool takes Python code string and PowerPoint file path as inputs.
        3.  ✅ Executes code in controlled environment with `prs` object available.
        4.  ✅ Captures and returns `stdout`, `stderr`, exceptions, and execution time as JSON.
        5.  ✅ **Security:** File path validation, path traversal prevention, file type checking.
        6.  ✅ Comprehensive error handling for syntax errors, runtime errors, and file issues.
        7.  ✅ Context injection includes `prs`, `pptx` module, `Path`, and `print` function.
    *   **MCP Concepts Used:** Tools, FastMCP framework.
    *   **Test Results:** 8/8 unit tests passing, 7/7 live tests passing (100% success rate).
    *   **Priority:** **CRITICAL.** This is the agent's "hands."

*   **MEP-003: Root and Resource Management** ✅ **COMPLETED**
    *   **Goal:** Allow the user to specify which presentation file(s) the agent can work on.
    *   **Implementation Notes:**
        1.  ✅ Implemented root scanning and automatic presentation loading from client-provided roots using a session-based, thread-safe architecture.
        2.  ✅ Refactored `execute_python_code` tool to remove `file_path` parameter - now uses the pre-loaded presentation from the session context.
        3.  ✅ Implemented `@mcp.resource("pptx://presentation")` endpoint that returns `prs.get_tree()` output as JSON.
        4.  ✅ Added comprehensive error handling for scenarios where no `.pptx` files are found in roots.
        5.  ✅ **Security:** Maintains file path validation and prevents directory traversal.
        6.  ✅ Context injection now includes `json` module for easier data formatting.
    *   **MCP Concepts Used:** Roots, Resources (via @mcp.resource decorator), session management.
    *   **Test Results:** 20/20 unit tests passing (enhanced from 5 working tests), 5/5 live tests passing (100% success rate after architectural fixes). Includes comprehensive session management, edge cases, and validation testing.
    *   **Priority:** **CRITICAL.** This makes the server dynamic, secure, and user-configurable.

*   **MEP-004: Unified "Save" and "Save As" Tool** ✅ **COMPLETED**
    *   **Goal:** Implement a single, secure tool to persist the in-memory presentation to disk, completing the core agentic workflow.
    *   **Implementation Notes:**
        1.  ✅ Created the **`save_presentation(output_path: str | None = None)` tool**.
        2.  ✅ If `output_path` is `None`, the tool overwrites the original file (retrieved from session context).
        3.  ✅ If `output_path` is provided, the tool saves a copy to the new path.
        4.  ✅ **Security:** All target paths (original or new) are validated to be within the client-provided `roots`.
        5.  ✅ Comprehensive error handling for permission errors, directory creation, and path validation.
        6.  ✅ Updates session state appropriately for Save As operations.
        7.  ✅ Fixed critical bug with `FileUrl` string conversion in path validation.
    *   **MCP Concepts Used:** Tools with optional arguments, path validation, session state management.
    *   **Test Results:** 14/14 unit tests passing, 7/7 live tests passing (100% success rate).
    *   **Priority:** **CRITICAL.** This makes the agent's work useful and persistent.

#### **Tier 2: Enhancing Agentic Capabilities (The "Smart" Layer)**

These MEPs make the agent more powerful and user-friendly.

*   **MEP-005: User-Guided Actions via Prompts**
    *   **Status:** Pending.
    *   **Goal:** Create pre-canned, user-controllable workflows for common tasks.
    *   **Scope:**
        1.  Implement the `prompts` capability.
        2.  Create several prompts, for example:
            *   **`create_title_slide(title: str, subtitle: str)`:** Generates the Python code to create a new presentation with a title slide.
            *   **`summarize_presentation()`:** Generates code that iterates through all slides, calls `get_tree()`, and produces a summary.
            *   **`apply_theme_color(color_name: str, element_path: str)`:** Generates code to change the color of a specific element.
    *   **MCP Concepts Used:** Prompts.
    *   **Priority:** **MEDIUM.** This improves usability for human users interacting with the agent.

*   **MEP-006: The Feedback Loop (`provide_feedback` Tool)**
    *   **Status:** Pending.
    *   **Goal:** Implement the "Learn" phase of the agentic workflow.
    *   **Scope:**
        1.  Create the **`provide_feedback(feedback_text: str, is_success: bool)` tool**.
        2.  The server-side implementation will log this structured feedback for developer review.
    *   **MCP Concepts Used:** Tools.
    *   **Priority:** **MEDIUM.** This is crucial for long-term improvement.

#### **Tier 3: Advanced and Future Systems**

These MEPs focus on making the toolkit smarter and providing deeper context.

*   **MEP-007: The Expert Assistant (`ask_expert` Tool)**
    *   **Status:** Pending.
    *   **Goal:** Implement the "Senior Developer on Call" for the agent.
    *   **Scope:**
        1.  Create the **`ask_expert(question: str)` tool**.
        2.  On the server, this tool will call a separate, specialized LLM instance primed with the `python-pptx` source code and documentation to provide high-quality, code-first answers.
    *   **MCP Concepts Used:** Tools, potentially Sampling.
    *   **Priority:** **LOW.** This is an advanced feature for agent autonomy.

*   **MEP-008: Visual Feedback (`render_slide` Tool)**
    *   **Status:** Future (Moonshot).
    *   **Goal:** Implement the "Visual See" tool for VLMs.
    *   **Scope:**
        1.  Create a new tool: **`render_slide(slide_index: int)`**.
        2.  This tool will call the (future) `prs.slides[slide_index].render_as_image()` method from the library FEPs.
        3.  It will return the image data as a structured tool output (base64-encoded with MIME type).
    *   **MCP Concepts Used:** Tools, Structured Tool Output.
    *   **Priority:** **LOW.** This is dependent on a major library enhancement.