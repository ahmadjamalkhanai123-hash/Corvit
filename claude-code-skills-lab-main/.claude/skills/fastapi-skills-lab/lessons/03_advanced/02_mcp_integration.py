"""
LESSON 12: MCP Server Integration & Browser Automation
======================================================

Learn how to create MCP (Model Context Protocol) servers that
integrate with FastAPI and browser automation.

What is MCP?
------------
MCP is a protocol that allows AI assistants (like Claude) to interact
with external tools and services. Think of it as a bridge between AI
and real-world capabilities.

Key Concepts:
- MCP Server: Provides tools to AI assistants
- Tools: Functions the AI can call
- Resources: Data the AI can access
- Browser-use: Library for browser automation with AI

To run the MCP server:
    uv run python -m src.app.mcp_server

To use with Claude Desktop, add to your config:
    Windows: %APPDATA%/Claude/claude_desktop_config.json
    macOS: ~/Library/Application Support/Claude/claude_desktop_config.json

    {
        "mcpServers": {
            "fastapi-browser": {
                "command": "uv",
                "args": ["run", "python", "-m", "src.app.mcp_server"],
                "cwd": "C:/path/to/fastapi-skills-lab"
            }
        }
    }
"""

# ============================================================
# PART 1: Understanding MCP Server Basics
# ============================================================

"""
MCP SERVER STRUCTURE:
--------------------

1. Server Instance
   - Create a Server with a name
   - Handles communication with AI clients

2. Tools
   - Define with @server.list_tools()
   - Each tool has: name, description, inputSchema
   - Called via @server.call_tool()

3. Resources (optional)
   - Static data AI can read
   - Like files or databases

4. Communication
   - Usually via stdio (stdin/stdout)
   - Can also use HTTP/WebSocket
"""

# Example: Simple MCP Server

SIMPLE_MCP_SERVER = '''
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Create server
server = Server("my-mcp-server")

# List available tools
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="greet",
            description="Greet a user by name",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"}
                },
                "required": ["name"]
            }
        )
    ]

# Handle tool calls
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "greet":
        user_name = arguments.get("name", "World")
        return [TextContent(type="text", text=f"Hello, {user_name}!")]
    return [TextContent(type="text", text="Unknown tool")]

# Run server
async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
'''


# ============================================================
# PART 2: Integrating FastAPI with MCP
# ============================================================

"""
FASTAPI + MCP INTEGRATION:
-------------------------

You can:
1. Create an MCP server that calls your FastAPI endpoints
2. Run both servers simultaneously
3. Use MCP for AI-facing interface, FastAPI for web interface

Example architecture:

    Claude Desktop
         │
         ▼
    MCP Server (stdio)
         │
         ▼
    FastAPI API (HTTP)
         │
         ▼
    Database / Services
"""

FASTAPI_MCP_INTEGRATION = '''
# mcp_fastapi_bridge.py
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

server = Server("fastapi-bridge")
FASTAPI_URL = "http://localhost:8000"

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="create_item",
            description="Create a new item in the FastAPI database",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "price": {"type": "number"},
                    "description": {"type": "string"}
                },
                "required": ["title", "price"]
            }
        ),
        Tool(
            name="list_items",
            description="List all items from FastAPI",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    async with httpx.AsyncClient() as client:
        if name == "create_item":
            # You would need a valid token in production
            response = await client.post(
                f"{FASTAPI_URL}/api/v1/items",
                json=arguments,
                headers={"Authorization": "Bearer YOUR_TOKEN"}
            )
            return [TextContent(type="text", text=f"Created: {response.json()}")]

        elif name == "list_items":
            response = await client.get(f"{FASTAPI_URL}/api/v1/items")
            return [TextContent(type="text", text=f"Items: {response.json()}")]
'''


# ============================================================
# PART 3: Browser Automation with browser-use
# ============================================================

"""
BROWSER-USE LIBRARY:
-------------------

browser-use is an AI-powered browser automation library.
It combines:
- Playwright (browser control)
- LLM (decision making)
- Vision (screenshot analysis)

Key features:
- Natural language task descriptions
- Automatic element detection
- Error recovery
- Multi-step workflows
"""

BROWSER_USE_EXAMPLE = '''
# browser_automation.py
from browser_use import Agent
from langchain_openai import ChatOpenAI
import asyncio

async def search_and_extract():
    """Example: Search and extract information."""

    agent = Agent(
        task="""
        1. Go to Google
        2. Search for 'FastAPI tutorial'
        3. Click on the first result
        4. Extract the main heading and first paragraph
        """,
        llm=ChatOpenAI(model="gpt-4o")
    )

    result = await agent.run()
    print(result)

# Direct Playwright usage (simpler, no LLM)
from playwright.async_api import async_playwright

async def simple_scrape(url: str):
    """Scrape without AI."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        title = await page.title()
        heading = await page.inner_text("h1")

        await browser.close()
        return {"title": title, "heading": heading}
'''


# ============================================================
# PART 4: Production MCP Server with FastAPI
# ============================================================

"""
PRODUCTION CONSIDERATIONS:
-------------------------

1. Error Handling
   - Catch all exceptions in tool handlers
   - Return meaningful error messages

2. Authentication
   - Store tokens securely
   - Use environment variables
   - Implement token refresh

3. Rate Limiting
   - Track requests to external services
   - Implement backoff strategies

4. Logging
   - Log all tool calls
   - Monitor for errors
   - Track usage patterns

5. Testing
   - Unit test each tool handler
   - Integration test with FastAPI
   - Mock external services
"""

PRODUCTION_MCP_EXAMPLE = '''
# production_mcp_server.py
import asyncio
import logging
import os
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
API_TOKEN = os.getenv("API_TOKEN", "")

server = Server("production-mcp")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="api_request",
            description="Make authenticated requests to FastAPI",
            inputSchema={
                "type": "object",
                "properties": {
                    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE"]},
                    "endpoint": {"type": "string"},
                    "data": {"type": "object"}
                },
                "required": ["method", "endpoint"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    logger.info(f"Tool called: {name} with args: {arguments}")

    try:
        if name == "api_request":
            return await handle_api_request(
                arguments.get("method", "GET"),
                arguments.get("endpoint", "/"),
                arguments.get("data")
            )
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]

    return [TextContent(type="text", text="Unknown tool")]

async def handle_api_request(method: str, endpoint: str, data: dict | None):
    """Make an authenticated API request."""
    url = f"{FASTAPI_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, headers=headers)
        elif method == "POST":
            response = await client.post(url, json=data, headers=headers)
        elif method == "PUT":
            response = await client.put(url, json=data, headers=headers)
        elif method == "DELETE":
            response = await client.delete(url, headers=headers)
        else:
            return [TextContent(type="text", text=f"Unknown method: {method}")]

        return [TextContent(
            type="text",
            text=f"Status: {response.status_code}\\nResponse: {response.text}"
        )]
'''

print("""
============================================================
MCP + FastAPI + Browser Automation
============================================================

This lesson covers:
1. MCP Server basics
2. FastAPI integration
3. Browser automation with browser-use
4. Production considerations

Quick Start:
-----------

1. Install Playwright browsers:
   playwright install

2. Set environment variables:
   OPENAI_API_KEY=your-key (for browser-use)

3. Run the MCP server:
   uv run python -m src.app.mcp_server

4. Configure Claude Desktop (see file header)

5. Ask Claude to use your tools!

See src/app/mcp_server.py for the full implementation.
""")
