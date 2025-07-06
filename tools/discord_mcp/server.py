"""
Discord MCP Server - Main Entry Point

Run this script:
cd discord_agent
uv --directory discord_mcp/ run server

This is the main entry point for the Discord MCP server. It coordinates
the Discord bot, MCP server, and tool registration.
"""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from .bot import start_bot, on_ready
from .tools import register_tools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("discord-mcp-server")


async def main():
    """
    Main entry point for the Discord MCP server.
    Starts the Discord bot and MCP server concurrently.
    """
    # Create MCP server instance
    app = Server("discord-server")
    
    # Register all tools with the MCP server
    register_tools(app)
    
    # Start the Discord bot
    await start_bot()

    # Start the MCP server with stdio transport
    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP Stdio Server: Starting Discord bot.")
        await on_ready()
        logger.info("MCP Stdio Server: Run loop started.")
        await app.run(read_stream, write_stream, app.create_initialization_options())
        logger.info("MCP Stdio Server: Run loop finished.")


if __name__ == "__main__":
    asyncio.run(main())