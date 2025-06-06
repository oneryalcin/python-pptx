# CLAUDE.md - Python-PPTX Development Router

AI assistant guide for the python-pptx project. This project has multiple development contexts with different workflows and patterns.

## 🎯 **Choose Your Development Context**

### **FEP Development (Feature Enhancement Proposals)**
**For:** Library introspection capabilities, `to_dict()` methods, `get_tree()` functionality, core python-pptx features

📁 **Guide:** [`src/CLAUDE.md`](src/CLAUDE.md)

**When to use:**
- Adding introspection to python-pptx classes
- Implementing `to_dict()` methods for shapes, slides, presentations
- Working on `get_tree()` hierarchical discovery
- Enhancing core library functionality
- Unit testing with mock objects and live scripts

**Example tasks:**
- "Add introspection to AutoShape class"
- "Implement to_dict for Chart objects" 
- "Create get_tree method for PlaceholderFormat"

---

### **MEP Development (MCP Enhancement Proposals)**
**For:** MCP server tools, AI agent interaction, protocol implementation

📁 **Guide:** [`mcp_server/CLAUDE.md`](mcp_server/CLAUDE.md)

**When to use:**
- Creating MCP server tools for AI agents
- Implementing FastMCP server functionality
- Building client-server protocol interactions
- Testing MCP protocol compliance
- Creating tools that expose python-pptx to AI agents

**Example tasks:**
- "Create execute_python_code MCP tool"
- "Add file resource management to MCP server"
- "Implement presentation loading tool for agents"

---

## 🔍 **Quick Context Detection**

**Keywords that indicate FEP context:**
- `to_dict`, `get_tree`, introspection
- BaseShape, Slide, Presentation classes
- Mock testing, live scripts
- Library enhancement, core functionality

**Keywords that indicate MEP context:**
- MCP server, FastMCP, tools
- Client-server, protocol, stdio transport
- AI agent, tool execution
- `@mcp.tool()`, async/await patterns

---

## 📋 **Project Structure Overview**

```
python-pptx/
├── CLAUDE.md                  # This router file
├── src/
│   ├── CLAUDE.md             # FEP development guide
│   └── pptx/                 # Core library code
├── mcp_server/
│   ├── CLAUDE.md             # MEP development guide  
│   ├── server/               # MCP server implementation
│   └── tests/                # MCP protocol tests
├── tests/                    # Core library tests
└── features/                 # BDD tests
```

---

## 🚀 **Getting Started**

1. **Identify your task type** using the context detection above
2. **Navigate to the appropriate guide**:
   - FEP work → [`src/CLAUDE.md`](src/CLAUDE.md)
   - MEP work → [`mcp_server/CLAUDE.md`](mcp_server/CLAUDE.md)
3. **Follow the specific workflow** for your development context
4. **Update the relevant roadmap**:
   - FEP progress → `ROADMAP.md`
   - MEP progress → `ROADMAP_MEP.md`

---

## 📚 **Additional Resources**

### **Roadmaps**
- **[ROADMAP.md](ROADMAP.md)** - FEP completion tracking and introspection features
- **[ROADMAP_MEP.md](ROADMAP_MEP.md)** - MEP completion tracking and server tools

### **Testing**
- **FEP Tests:** `tests/introspection/` (unit) + `live_test_*.py` scripts
- **MEP Tests:** `mcp_server/tests/` (unit + live MCP protocol tests)

### **Documentation**
- **Library Docs:** `docs/` directory
- **API Reference:** Generated from docstrings and type hints
- **Examples:** `features/` directory with BDD scenarios

---

## ⚡ **Quick Commands**

```bash
# FEP Development
source venv/bin/activate && python -m pytest tests/introspection/ -v
python live_test_*.py

# MEP Development  
source venv/bin/activate && python -m pytest mcp_server/tests/ -v
python mcp_server/tests/live_test_mcp_server.py

# Both contexts
source venv/bin/activate && pip install -e . && pip install -r requirements-dev.txt

# PR Code Review
# Fetch and display all PR comments in readable format (replace PR_NUMBER)
gh api repos/oneryalcin/python-pptx/pulls/PR_NUMBER/comments --paginate | jq -r '.[] | "File: \(.path), Line: \(.original_line // .line // "N/A"), Comment: \(.body)"'
```

---

*This router ensures you get the right development workflow for your specific task context.*