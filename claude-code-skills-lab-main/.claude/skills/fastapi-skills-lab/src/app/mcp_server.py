"""
MCP Server Integration with FastAPI
===================================

This module demonstrates how to integrate Model Context Protocol (MCP)
with FastAPI for browser automation capabilities.

MCP enables AI assistants to interact with external tools and services.
Combined with browser-use, it allows browser automation.

To run the MCP server:
    uv run python -m src.app.mcp_server

Or integrate with Claude Desktop by adding to config:
    {
        "mcpServers": {
            "fastapi-browser": {
                "command": "uv",
                "args": ["run", "python", "-m", "src.app.mcp_server"]
            }
        }
    }
"""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Create MCP server instance
server = Server("fastapi-browser-mcp")


# Define available tools
@server.list_tools()
async def list_tools():
    """List available MCP tools."""
    return [
        Tool(
            name="search_web",
            description="Search the web using a browser and return results",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="browse_url",
            description="Navigate to a URL and extract page content",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="take_screenshot",
            description="Take a screenshot of the current page",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to screenshot (optional, uses current page if not provided)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="extract_data",
            description="Extract structured data from a webpage",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract data from"
                    },
                    "selectors": {
                        "type": "object",
                        "description": "CSS selectors for data extraction"
                    }
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="api_health_check",
            description="Check the health of the FastAPI server",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_url": {
                        "type": "string",
                        "description": "The FastAPI server URL",
                        "default": "http://localhost:8000"
                    }
                },
                "required": []
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""

    if name == "search_web":
        return await handle_search_web(arguments.get("query", ""))

    elif name == "browse_url":
        return await handle_browse_url(arguments.get("url", ""))

    elif name == "take_screenshot":
        return await handle_take_screenshot(arguments.get("url"))

    elif name == "extract_data":
        return await handle_extract_data(
            arguments.get("url", ""),
            arguments.get("selectors", {})
        )

    elif name == "api_health_check":
        return await handle_api_health_check(
            arguments.get("api_url", "http://localhost:8000")
        )

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def handle_search_web(query: str):
    """Perform a web search using browser-use."""
    try:
        from browser_use import Agent
        from langchain_openai import ChatOpenAI

        # Note: You need to set OPENAI_API_KEY environment variable
        # Or use a different LLM provider

        agent = Agent(
            task=f"Search the web for: {query}. Return the top 5 results with titles and URLs.",
            llm=ChatOpenAI(model="gpt-4o-mini")
        )

        result = await agent.run()
        return [TextContent(type="text", text=str(result))]

    except ImportError as e:
        return [TextContent(
            type="text",
            text=f"browser-use not fully configured. Error: {e}\n\n"
                 "To use browser automation, ensure you have:\n"
                 "1. Installed playwright: playwright install\n"
                 "2. Set OPENAI_API_KEY environment variable"
        )]
    except Exception as e:
        return [TextContent(type="text", text=f"Search failed: {str(e)}")]


async def handle_browse_url(url: str):
    """Navigate to URL and extract content using playwright."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")

            # Extract page content
            title = await page.title()
            content = await page.inner_text("body")

            # Truncate if too long
            if len(content) > 5000:
                content = content[:5000] + "...[truncated]"

            await browser.close()

            return [TextContent(
                type="text",
                text=f"Title: {title}\n\nContent:\n{content}"
            )]

    except Exception as e:
        return [TextContent(type="text", text=f"Browse failed: {str(e)}")]


async def handle_take_screenshot(url: str | None):
    """Take a screenshot of a webpage."""
    try:
        from playwright.async_api import async_playwright
        import base64

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            if url:
                await page.goto(url, wait_until="networkidle")

            screenshot = await page.screenshot(type="png")
            screenshot_b64 = base64.b64encode(screenshot).decode()

            await browser.close()

            return [TextContent(
                type="text",
                text=f"Screenshot captured (base64, first 100 chars): {screenshot_b64[:100]}...\n"
                     f"Full length: {len(screenshot_b64)} characters"
            )]

    except Exception as e:
        return [TextContent(type="text", text=f"Screenshot failed: {str(e)}")]


async def handle_extract_data(url: str, selectors: dict):
    """Extract structured data from a webpage."""
    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, wait_until="domcontentloaded")

            data = {}

            # Default selectors if none provided
            if not selectors:
                selectors = {
                    "title": "h1",
                    "paragraphs": "p",
                    "links": "a"
                }

            for key, selector in selectors.items():
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        texts = []
                        for el in elements[:10]:  # Limit to 10 elements
                            text = await el.inner_text()
                            texts.append(text.strip())
                        data[key] = texts
                except Exception:
                    data[key] = f"Could not extract with selector: {selector}"

            await browser.close()

            return [TextContent(
                type="text",
                text=f"Extracted data from {url}:\n{json.dumps(data, indent=2)}"
            )]

    except Exception as e:
        return [TextContent(type="text", text=f"Extraction failed: {str(e)}")]


async def handle_api_health_check(api_url: str):
    """Check FastAPI server health."""
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/health", timeout=5)

            return [TextContent(
                type="text",
                text=f"API Health Check for {api_url}:\n"
                     f"Status Code: {response.status_code}\n"
                     f"Response: {response.json()}"
            )]

    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Health check failed for {api_url}: {str(e)}"
        )]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
