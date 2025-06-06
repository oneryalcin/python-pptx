#!/usr/bin/env python3
"""
Demonstration script for MEP-002: execute_python_code tool.

This script shows how the execute_python_code tool works in practice,
demonstrating various scenarios including successful execution, error handling,
and real-world use cases with PowerPoint presentations.

Usage:
    python mcp_server/tests/demo_execute_python_code.py

Requirements:
    - Virtual environment must be activated
    - MCP dependencies must be installed
    - A test PowerPoint file must be available
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the project root to Python path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import MCP client functionality
try:
    from mcp import types
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client
except ImportError as e:
    print(f"Error: Could not import MCP client libraries: {e}")
    print("Please ensure MCP dependencies are installed with:")
    print("  pip install -r requirements-dev.txt")
    sys.exit(1)


class ExecutePythonCodeDemo:
    """Demo class for showcasing the execute_python_code tool."""

    def __init__(self):
        self.server_path = PROJECT_ROOT / "mcp_server" / "server" / "main.py"
        self.test_file = PROJECT_ROOT / "tests" / "test_files" / "minimal.pptx"

    def print_banner(self, title: str):
        """Print a nice banner for section headers."""
        print(f"\n{'=' * 60}")
        print(f"  {title}")
        print(f"{'=' * 60}")

    def print_result(self, result_json: str, description: str):
        """Print formatted result from the tool."""
        try:
            data = json.loads(result_json)
            print(f"\n📋 {description}")
            print(f"   Success: {data.get('success', 'N/A')}")
            print(f"   Execution Time: {data.get('execution_time', 'N/A'):.4f}s")
            
            if data.get("stdout"):
                print(f"   📤 Stdout:")
                for line in data["stdout"].strip().split('\n'):
                    print(f"      {line}")
            
            if data.get("stderr"):
                print(f"   📤 Stderr:")
                for line in data["stderr"].strip().split('\n'):
                    print(f"      {line}")
            
            if data.get("error"):
                print(f"   ❌ Error: {data['error']}")
                
        except json.JSONDecodeError:
            print(f"   ❌ Invalid JSON response: {result_json[:100]}...")

    async def demo_successful_execution(self, session):
        """Demonstrate successful code execution."""
        self.print_banner("Demo 1: Successful Code Execution")
        
        # Basic presentation info
        code1 = """
print("=== Presentation Overview ===")
print(f"Number of slides: {len(prs.slides)}")
print(f"Number of slide masters: {len(prs.slide_masters)}")
print(f"Slide layouts available: {len(prs.slide_layouts)}")

# Show first slide info if available
if prs.slides:
    slide = prs.slides[0]
    print(f"\\nFirst slide has {len(slide.shapes)} shapes")
"""
        
        result = await session.call_tool("execute_python_code", arguments={
            "code": code1,
            "file_path": str(self.test_file)
        })
        
        if result.content:
            self.print_result(result.content[0].text, "Basic presentation information")

    async def demo_introspection_capabilities(self, session):
        """Demonstrate introspection capabilities."""
        self.print_banner("Demo 2: Introspection Capabilities")
        
        # Using introspection features
        code2 = """
# Try to use introspection if available
print("=== Introspection Demo ===")

# Check if get_tree method is available
if hasattr(prs, 'get_tree'):
    print("✅ get_tree() method is available!")
    tree = prs.get_tree()
    print(f"Tree structure: {tree[:200]}...")  # Show first 200 chars
else:
    print("❌ get_tree() method not available yet")

# Basic slide inspection
if prs.slides:
    slide = prs.slides[0]
    print(f"\\nSlide 0 inspection:")
    print(f"  - Layout: {slide.slide_layout.name if slide.slide_layout else 'N/A'}")
    print(f"  - Shapes: {len(slide.shapes)}")
    
    # Inspect first shape if available
    if slide.shapes:
        shape = slide.shapes[0]
        print(f"  - First shape type: {type(shape).__name__}")
        print(f"  - Shape has text: {hasattr(shape, 'text')}")
"""
        
        result = await session.call_tool("execute_python_code", arguments={
            "code": code2,
            "file_path": str(self.test_file)
        })
        
        if result.content:
            self.print_result(result.content[0].text, "Introspection capabilities")

    async def demo_error_handling(self, session):
        """Demonstrate error handling capabilities."""
        self.print_banner("Demo 3: Error Handling")
        
        # Syntax error
        print("\n🔸 Testing syntax error handling:")
        result = await session.call_tool("execute_python_code", arguments={
            "code": "if True print('missing colon')",
            "file_path": str(self.test_file)
        })
        
        if result.content:
            self.print_result(result.content[0].text, "Syntax error test")

        # Runtime error
        print("\n🔸 Testing runtime error handling:")
        result = await session.call_tool("execute_python_code", arguments={
            "code": "raise ValueError('This is a demo runtime error')",
            "file_path": str(self.test_file)
        })
        
        if result.content:
            self.print_result(result.content[0].text, "Runtime error test")

        # File not found error
        print("\n🔸 Testing file not found error:")
        result = await session.call_tool("execute_python_code", arguments={
            "code": "print('test')",
            "file_path": "nonexistent_file.pptx"
        })
        
        if result.content:
            self.print_result(result.content[0].text, "File not found test")

    async def demo_advanced_operations(self, session):
        """Demonstrate advanced operations."""
        self.print_banner("Demo 4: Advanced Operations")
        
        # Advanced presentation analysis
        code3 = """
import sys
from pathlib import Path

print("=== Advanced Operations Demo ===")

# Demonstrate that we have access to additional modules
print(f"Python version: {sys.version_info.major}.{sys.version_info.minor}")
print(f"Available modules in context: pptx, Path, print")

# File system operations with Path
pptx_file = Path("minimal.pptx")  # Demonstrate Path is available
print(f"Working with Path objects: {pptx_file.suffix}")

# Complex presentation analysis
print(f"\\n=== Detailed Presentation Analysis ===")
total_shapes = 0
for i, slide in enumerate(prs.slides):
    shape_count = len(slide.shapes)
    total_shapes += shape_count
    print(f"Slide {i+1}: {shape_count} shapes")
    
    # Analyze shape types
    shape_types = {}
    for shape in slide.shapes:
        shape_type = type(shape).__name__
        shape_types[shape_type] = shape_types.get(shape_type, 0) + 1
    
    if shape_types:
        print(f"  Shape types: {dict(shape_types)}")

print(f"\\nTotal shapes across all slides: {total_shapes}")

# Test stderr output
print("This goes to stderr", file=sys.stderr)
"""
        
        result = await session.call_tool("execute_python_code", arguments={
            "code": code3,
            "file_path": str(self.test_file)
        })
        
        if result.content:
            self.print_result(result.content[0].text, "Advanced operations")

    async def demo_discovery_inspect_act_workflow(self, session):
        """Demonstrate the Discover -> Inspect -> Act workflow."""
        self.print_banner("Demo 5: Discovery -> Inspect -> Act Workflow")
        
        # Workflow demonstration
        code4 = """
print("=== Discover -> Inspect -> Act Workflow ===")

# DISCOVER: Find what's in the presentation
print("\\n🔍 DISCOVER Phase:")
print(f"📊 Found {len(prs.slides)} slides to analyze")
print(f"🎨 Found {len(prs.slide_masters)} slide masters")

# INSPECT: Look at specific elements
print("\\n🔍 INSPECT Phase:")
for i, slide in enumerate(prs.slides):
    print(f"\\n📄 Slide {i+1} details:")
    print(f"   - Shapes: {len(slide.shapes)}")
    
    # Inspect each shape
    for j, shape in enumerate(slide.shapes):
        shape_info = f"Shape {j+1}: {type(shape).__name__}"
        
        # Try to get more specific info
        try:
            if hasattr(shape, 'shape_type'):
                shape_info += f" (type: {shape.shape_type})"
        except:
            pass
            
        try:
            if hasattr(shape, 'text'):
                text_preview = shape.text[:50] if shape.text else "No text"
                shape_info += f" - Text: '{text_preview}'"
        except:
            pass
            
        print(f"   - {shape_info}")

# ACT: Show what we could do (without actually modifying)
print("\\n🎯 ACT Phase (simulation):")
print("   ✅ Could add new slides")
print("   ✅ Could modify text content")
print("   ✅ Could analyze and report on content")
print("   ✅ Could create summary reports")
print("   ✅ Could validate presentation structure")

print("\\n🎉 Workflow completed successfully!")
"""
        
        result = await session.call_tool("execute_python_code", arguments={
            "code": code4,
            "file_path": str(self.test_file)
        })
        
        if result.content:
            self.print_result(result.content[0].text, "Complete workflow demonstration")

    async def run_demo(self):
        """Run the complete demonstration."""
        print("🎬 Starting MEP-002 execute_python_code Tool Demonstration")
        print(f"📁 Using test file: {self.test_file}")
        
        if not self.test_file.exists():
            print(f"❌ Test file not found: {self.test_file}")
            print("Please ensure the test file exists before running the demo.")
            return False

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

                    # Run all demos
                    await self.demo_successful_execution(session)
                    await self.demo_introspection_capabilities(session)
                    await self.demo_error_handling(session)
                    await self.demo_advanced_operations(session)
                    await self.demo_discovery_inspect_act_workflow(session)

            print(f"\n{'=' * 60}")
            print("🎉 Demo completed successfully!")
            print("The execute_python_code tool is working correctly and ready for use.")
            print(f"{'=' * 60}")
            return True

        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            return False


async def main():
    """Run the demonstration."""
    demo = ExecutePythonCodeDemo()
    success = await demo.run_demo()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)