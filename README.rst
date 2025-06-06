*python-pptx* is a Python library for creating, reading, and updating PowerPoint (.pptx)
files.

A typical use would be generating a PowerPoint presentation from dynamic content such as
a database query, analytics output, or a JSON payload, perhaps in response to an HTTP
request and downloading the generated PPTX file in response. It runs on any Python
capable platform, including macOS and Linux, and does not require the PowerPoint
application to be installed or licensed.

It can also be used to analyze PowerPoint files from a corpus, perhaps to extract search
indexing text and images.

It can also be used to simply automate the production of a slide or two that would be
tedious to get right by hand, which is how this all got started.

More information is available in the `python-pptx documentation`_.

Browse `examples with screenshots`_ to get a quick idea what you can do with
python-pptx.

MCP Server for AI Agents
-------------------------

python-pptx includes an MCP (Model Context Protocol) server that enables AI agents
like Claude to work with PowerPoint presentations. The server provides AI agents with
essential context and tools for safe, effective presentation manipulation.

Installation for MCP
~~~~~~~~~~~~~~~~~~~~~

Install the MCP server dependencies::

    pip install -r requirements-dev.txt

Configuration for Claude Desktop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add to your Claude Desktop configuration::

    {
      "mcpServers": {
        "python-pptx": {
          "command": "python",
          "args": ["/path/to/python-pptx/mcp_server/server/main.py"],
          "env": {}
        }
      }
    }

Available Tools
~~~~~~~~~~~~~~~

* **get_info**: Essential onboarding tool providing AI agents with python-pptx usage patterns and examples

Usage
~~~~~

AI agents must call ``get_info`` first to receive proper context and examples for working with presentations safely and effectively.

.. _`python-pptx documentation`:
   https://python-pptx.readthedocs.org/en/latest/

.. _`examples with screenshots`:
   https://python-pptx.readthedocs.org/en/latest/user/quickstart.html
