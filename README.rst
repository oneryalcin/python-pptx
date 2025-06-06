**AI-Enhanced python-pptx Fork**

This is a specialized fork of the *python-pptx* library designed to be **AI/LLM/Agent-friendly**. 
While maintaining full compatibility with the original python-pptx API, this fork adds powerful 
introspection capabilities and an MCP (Model Context Protocol) server to enable AI agents 
like Claude, GPT, and others to work effectively with PowerPoint presentations.

**Why This Fork?**

The original python-pptx is excellent for programmatic PowerPoint manipulation, but AI agents 
struggle with it because:

* **Limited Discoverability**: No way to explore presentation structure without prior knowledge
* **Opaque Objects**: Shape and slide contents are not easily inspectable
* **Trial-and-Error Development**: Agents must guess object properties and relationships

This fork solves these problems through two major enhancement initiatives:

**🔍 FEPs (Feature Enhancement Proposals)**: Core library introspection capabilities

* ``get_tree()`` methods for hierarchical content discovery
* ``to_dict()`` methods for detailed object inspection  
* ``to_dict(fields=[...])`` for precise, efficient property access
* Enhanced transparency across all major object types

**🤖 MEPs (MCP Enhancement Proposals)**: AI agent server infrastructure

* MCP server for seamless AI agent integration
* Guided workflows and safety patterns
* Agent onboarding and context management
* Secure, sandboxed execution environment

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
2. **Install MCP Dependencies**: ``pip install -r requirements-dev.txt``
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

    pip install -r requirements-dev.txt

**Claude Desktop Configuration:**

.. code-block:: json

    {
      "mcpServers": {
        "python-pptx": {
          "command": "python",
          "args": ["/path/to/python-pptx/mcp_server/server/main.py"],
          "env": {}
        }
      }
    }

**Available Tools:**

* **get_info**: Essential onboarding providing usage patterns and examples (agents must call this first)

**Progress**: 1/7 MEPs completed - see `ROADMAP_MEP.md`_ for full server roadmap

**📚 Development & Documentation**

**For Contributors:**

* **FEP Development**: See `src/CLAUDE.md`_ for library enhancement workflows
* **MEP Development**: See `mcp_server/CLAUDE.md`_ for MCP server development
* **Context Router**: See `CLAUDE.md`_ for development context guidance

**Roadmap Status:**

* **FEP Progress**: Core introspection (✅), Typography (✅), Containers (✅), Advanced features (🚧)
* **MEP Progress**: Server bootstrap (✅), Execute tool (📋), Resource management (📋), Advanced tools (📋)

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
