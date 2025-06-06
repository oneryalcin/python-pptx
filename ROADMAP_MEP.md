While the `python-pptx` FEPs focus on *exposing* the data, the MCP server is what *packages and presents* that data to the AI agent. A well-designed server is just as critical as a well-designed introspection API.

Let's create a parallel roadmap for building our `python-pptx` MCP server, which we'll call **MEPs (MCP Enhancement Proposals)**. We'll use the same principles of iterative development and clear, focused goals.

---

### **Project Vision: The `pptx-agent-server` MCP Server**

**Core Goal:** To create a robust, secure, and intelligent MCP server that acts as the definitive bridge between an AI agent (like Claude Desktop, VS Code Copilot, etc.) and the `python-pptx` library. This server will not just expose data; it will provide a curated set of tools and resources that enable an agent to safely and effectively analyze, modify, and even create PowerPoint presentations.

**Guiding Principles (from the MCP documentation):**
1.  **User-Controlled vs. Model-Controlled:** We will clearly distinguish between features the user must explicitly invoke (like `Prompts`) and features the model can use autonomously (like `Tools`).
2.  **Security First:** The server will operate on a "least privilege" basis, especially concerning file system access.
3.  **Agent-Centric Design:** The tools and resources will be designed to support the "See -> Understand -> Act -> Learn" agentic workflow we've defined.

---

### **Definitive MEP Roadmap for the `pptx-agent-server`**

This roadmap is designed to be implemented in parallel with the `python-pptx` FEPs. Early MEPs can be built using the existing introspection capabilities, and later MEPs will leverage the more advanced features as they are completed.

#### **Tier 1: Core Functionality (The Foundation)**

These MEPs establish the basic server and its primary interaction tools.

*   **MEP-001: Server Bootstrap & `get_info` Tool** ✅ **COMPLETED**
    *   **Goal:** Create the basic Python MCP server structure and implement the mandatory "onboarding manual" tool.
    *   **Implementation Notes:**
        1.  ✅ Set up MCP server using official `mcp[cli]` package with FastMCP framework
        2.  ✅ Implemented server with proper FastMCP initialization and stdio transport
        3.  ✅ Created the **`get_info()` tool** with comprehensive error handling
        4.  ✅ Created static markdown document with corrected code examples (fixed `prs.slides[0].get_tree()` and `prs.slides[0].shapes[1]` patterns)
        5.  ✅ Directory structure: `mcp_server/` (renamed to avoid import conflicts)
    *   **MCP Concepts Used:** Tools, FastMCP Server, stdio transport.
    *   **Test Results:** 10/10 unit tests passing, 4/4 live tests passing (100% success rate)
    *   **Priority:** **CRITICAL.** This is the entry point for any agent interaction.

*   **MEP-002: The `execute_python_code` Tool** ✅ **COMPLETED**
    *   **Goal:** Create the primary "Act" tool that allows the agent to run `python-pptx` code.
    *   **Implementation Notes:**
        1.  ✅ Implemented the **`execute_python_code(code: str, file_path: str)` tool**
        2.  ✅ Tool takes Python code string and PowerPoint file path as inputs
        3.  ✅ Executes code in controlled environment with `prs` object available
        4.  ✅ Captures and returns `stdout`, `stderr`, exceptions, and execution time as JSON
        5.  ✅ **Security:** File path validation, path traversal prevention, file type checking
        6.  ✅ Comprehensive error handling for syntax errors, runtime errors, and file issues
        7.  ✅ Context injection includes `prs`, `pptx` module, `Path`, and `print` function
    *   **MCP Concepts Used:** Tools, FastMCP framework.
    *   **Test Results:** 21/21 unit tests passing, 7/7 live tests passing (100% success rate)
    *   **Priority:** **CRITICAL.** This is the agent's "hands."

*   **MEP-003: Root and Resource Management**
    *   **Goal:** Allow the user to specify which presentation file(s) the agent can work on.
    *   **Scope:**
        1.  Implement the `roots` capability. The server will respect the `file:///` URIs provided by the client (e.g., Claude Desktop's workspace) to identify the presentation file to load.
        2.  Implement the `resources/list` endpoint to expose the currently loaded presentation file as a resource.
        3.  Implement the `resources/read` endpoint. When an agent requests to "read" the presentation resource, instead of returning the binary, we will return the output of `prs.get_tree()`. This cleverly integrates our "Discovery" phase into the standard MCP resource model.
    *   **MCP Concepts Used:** Roots, Resources.
    *   **Priority:** **HIGH.** This makes the server dynamic and user-configurable.

#### **Tier 2: Enhancing Agentic Capabilities (The "Smart" Layer)**

These MEPs make the agent more powerful and user-friendly.

*   **MEP-004: Visual Feedback (`render_slide` Tool)**
    *   **Goal:** Implement the "Visual See" tool for VLMs.
    *   **Scope:**
        1.  Create a new tool: **`render_slide(slide_index: int)`**.
        2.  This tool will call the (future) `prs.slides[slide_index].render_as_image()` method from FEP-024.
        3.  It will return the image data as a structured tool output, likely as a base64-encoded string with a MIME type.
    *   **MCP Concepts Used:** Tools, Structured Tool Output.
    *   **Priority:** **MEDIUM.** This is a "moonshot" feature on the library side, but defining the tool now clarifies the vision.

*   **MEP-005: User-Guided Actions via Prompts**
    *   **Goal:** Create pre-canned, user-controllable workflows for common tasks.
    *   **Scope:**
        1.  Implement the `prompts` capability.
        2.  Create several prompts, for example:
            *   **`create_title_slide(title: str, subtitle: str)`:** Generates the Python code to create a new presentation with a title slide.
            *   **`summarize_presentation()`:** Generates code that iterates through all slides, calls `get_tree()`, and produces a summary.
            *   **`apply_theme_color(color_name: str, element_path: str)`:** Generates code to change the color of a specific element.
    *   **MCP Concepts Used:** Prompts.
    *   **Priority:** **MEDIUM.** This improves usability for human users interacting with the agent.

#### **Tier 3: Advanced and Self-Improving Systems**

These MEPs focus on making the toolkit smarter and providing a feedback loop for us.

*   **MEP-006: The Expert Assistant (`ask_expert` Tool)**
    *   **Goal:** Implement the "Senior Developer on Call" for the agent.
    *   **Scope:**
        1.  Create the **`ask_expert(question: str)` tool**.
        2.  On the server, this tool will make a call to a separate, specialized LLM instance (e.g., via an internal API).
        3.  This expert LLM will be primed with the `python-pptx` source code, our FEP roadmap, and other relevant documentation to provide high-quality, code-first answers to "how-to" questions.
    *   **MCP Concepts Used:** Tools.
    *   **Priority:** **LOW.** This is an advanced feature but incredibly powerful for agent autonomy.

*   **MEP-007: The Feedback Loop (`provide_feedback` Tool)**
    *   **Goal:** Implement the "Learn" phase of the agentic workflow.
    *   **Scope:**
        1.  Create the **`provide_feedback(feedback_text: str, is_success: bool)` tool**.
        2.  The server-side implementation will simply log this structured feedback to a designated location (e.g., a log file, a database, or a Slack channel) for the development team to review.
    *   **MCP Concepts Used:** Tools.
    *   **Priority:** **MEDIUM.** This is crucial for long-term improvement of both the library and the MCP server.

This MEP roadmap provides a clear, parallel path for the server development. We can start with MEP-001 and MEP-002 immediately, as they only depend on the existing `python-pptx` library. MEP-003 can then be built as soon as FEP-020 (`get_tree`) is complete. This ensures our server and library evolve in lockstep.