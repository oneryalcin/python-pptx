**AI-Enhanced python-pptx Fork**

This is a specialized fork of the *python-pptx* library designed to be **AI/LLM/Agent-friendly**. 
While maintaining full compatibility with the original python-pptx API, this fork adds powerful 
introspection capabilities and a production-ready MCP (Model Context Protocol) server that enables 
AI agents to safely and effectively manipulate PowerPoint presentations.

**Why This Fork?**

The original python-pptx is excellent for programmatic PowerPoint manipulation, but AI agents 
struggle with it because:

* **Limited Discoverability**: No way to explore presentation structure without prior knowledge
* **Opaque Objects**: Shape and slide contents are not easily inspectable  
* **Trial-and-Error Development**: Agents must guess object properties and relationships
* **No Agent Integration**: No standardized way for AI agents to interact with presentations

This fork solves these problems through two parallel enhancement initiatives:

**🔍 FEPs (Feature Enhancement Proposals)**: Core library introspection capabilities

* ``get_tree()`` methods for hierarchical content discovery
* ``to_dict()`` methods for detailed object inspection  
* ``to_dict(fields=[...])`` for precise, efficient property access
* Enhanced transparency across all major object types

**🤖 MEPs (MCP Enhancement Proposals)**: Production-ready AI agent server

* **Complete Agentic Workflow**: See → Understand → Act → Persist
* **Security-First Design**: Sandboxed execution with root-based file access control
* **Session Management**: Thread-safe, multi-client architecture  
* **Comprehensive Testing**: 100% test coverage with unit and live protocol tests

**Traditional Use Cases** (fully supported):

* Generating presentations from dynamic content (databases, APIs, JSON)
* Analyzing PowerPoint files for text and image extraction  
* Automating tedious slide production tasks
* Cross-platform operation without PowerPoint installation

**🚀 Getting Started**

**For Traditional Python Development:**

Browse `examples with screenshots`_ to see what you can do with the enhanced python-pptx.
More information is available in the `python-pptx documentation`_.

**For AI Agent Integration:**

1. **Review the Roadmaps**: See `ROADMAP.md`_ (FEPs) and `ROADMAP_MEP.md`_ (MEPs) for current capabilities
2. **Install MCP Dependencies**: ``pip install -r requirements-mcp.txt``
3. **Configure Your AI Client**: See MCP setup below

**🔍 Enhanced Introspection (FEPs)**

**Discover Content Structure:**

.. code-block:: python

    import pptx
    prs = pptx.Presentation('example.pptx')
    
    # Discover slide structure
    tree = prs.slides[0].get_tree()
    print(tree)  # Shows hierarchical content map
    
    # Inspect specific objects
    shape = prs.slides[0].shapes[1]
    details = shape.to_dict(fields=['properties.fill', 'geometry'])
    print(details)  # Detailed shape information

**Progress**: 19/22 FEPs completed (86.4% complete) - see `ROADMAP.md`_ for status

**🤖 MCP Server for AI Agents (MEPs)**

**Installation:**

.. code-block:: bash

    pip install -r requirements-mcp.txt

**Claude Desktop Configuration:**

.. code-block:: json

    {
      "mcpServers": {
        "python-pptx": {
          "command": "python",
          "args": ["/path/to/python-pptx/mcp_server/server/main.py"],
          "env": {},
          "roots": [
            "file:///path/to/your/presentations"
          ]
        }
      }
    }

**Available Tools:**

* **get_info()**: Essential onboarding providing usage patterns and examples (agents must call this first)
* **execute_python_code(code: str)**: Execute Python code with pre-loaded presentation object (``prs``)
* **save_presentation(output_path: str = None)**: Save presentation to original location or new path (parent directory must exist)

**Available Resources:**

* **pptx://presentation**: Access to ``prs.get_tree()`` output for content discovery

**Agentic Workflow:**

1. **See**: Call ``get_info()`` for context, access ``pptx://presentation`` resource for structure
2. **Understand**: Use ``execute_python_code()`` with exploratory code to analyze content  
3. **Act**: Use ``execute_python_code()`` to modify presentation (add slides, shapes, text, etc.)
4. **Persist**: Use ``save_presentation()`` to save changes

**Example Agent Interaction:**

.. code-block:: python

    # Agent workflow (via MCP client like Claude Desktop):
    
    # 1. See: Get orientation and discover structure
    info = await call_tool("get_info")  # Get usage patterns
    tree = await read_resource("pptx://presentation")  # Explore content
    
    # 2. Understand: Analyze presentation content
    result = await call_tool("execute_python_code", {
        "code": "print(f'Slides: {len(prs.slides)}'); print(prs.slides[0].get_tree())"
    })
    
    # 3. Act: Modify presentation  
    result = await call_tool("execute_python_code", {
        "code": """
        slide = prs.slides.add_slide(prs.slide_layouts[0])
        slide.shapes.title.text = 'AI-Generated Slide'
        slide.shapes.placeholders[1].text = 'Created by agent!'
        """
    })
    
    # 4. Persist: Save changes
    result = await call_tool("save_presentation")  # Save to original
    # OR: result = await call_tool("save_presentation", {"output_path": "backup.pptx"})

**Security Features:**

* **Root-based Access Control**: All file operations restricted to client-configured directories
* **Path Traversal Prevention**: Comprehensive path validation prevents unauthorized access
* **Sandboxed Execution**: Python code execution isolated with controlled context injection
* **Session Isolation**: Thread-safe, multi-client architecture with automatic cleanup

**Testing & Reliability:**

* **100% Test Coverage**: All tools and features comprehensively tested
* **52 Unit Tests**: Fast, isolated testing of individual components with comprehensive session management coverage
* **Live Protocol Tests**: End-to-end MCP client-server communication validation
* **Demo Scripts**: Interactive demonstrations of all capabilities

**Progress**: 4/7 MEPs completed (Tier 1 complete) - see `ROADMAP_MEP.md`_ for full server roadmap

**📚 Development & Documentation**

**For Contributors:**

* **FEP Development**: See `src/CLAUDE.md`_ for library enhancement workflows
* **MEP Development**: See `mcp_server/CLAUDE.md`_ for MCP server development
* **Context Router**: See `CLAUDE.md`_ for development context guidance

**Roadmap Status:**

* **FEP Progress**: Core introspection (✅), Typography (✅), Containers (✅), Advanced features (🚧)
* **MEP Progress**: 
  * **Tier 1 - Foundation** (✅): Server bootstrap, Execute tool, Root management, Save tool
  * **Tier 2 - Smart Layer** (📋): Prompts, Feedback loop, Expert assistant  
  * **Tier 3 - Advanced** (📋): Visual feedback and rendering capabilities

.. _`python-pptx documentation`:
   https://python-pptx.readthedocs.org/en/latest/

.. _`examples with screenshots`:
   https://python-pptx.readthedocs.org/en/latest/user/quickstart.html

.. _`ROADMAP.md`:
   https://github.com/oneryalcin/python-pptx/blob/master/ROADMAP.md

.. _`ROADMAP_MEP.md`:
   https://github.com/oneryalcin/python-pptx/blob/master/ROADMAP_MEP.md

.. _`src/CLAUDE.md`:
   https://github.com/oneryalcin/python-pptx/blob/master/src/CLAUDE.md

.. _`mcp_server/CLAUDE.md`:
   https://github.com/oneryalcin/python-pptx/blob/master/mcp_server/CLAUDE.md

.. _`CLAUDE.md`:
   https://github.com/oneryalcin/python-pptx/blob/master/CLAUDE.md
