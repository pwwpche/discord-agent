"""
MCP tool definitions and dispatcher for Discord server.
Contains tool schemas and the main routing logic for tool calls.
"""

import logging
from typing import Any, List

from mcp.server import Server
from mcp.types import Tool, TextContent

from .utils import require_discord_client
from .handlers import (
    handle_get_all_channels_across_servers,
    handle_fetch_server_with_channels,
    handle_fetch_channel_details,
    handle_read_messages_from_channel,
    handle_get_pinned_messages,
    handle_get_thread_details,
    handle_get_workspace_structure,
)

logger = logging.getLogger("discord-mcp-server")


def register_tools(app: Server):
    """Register all tools with the MCP server."""
    
    @app.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="list_channels",
                description="List all channels in the server",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "string",
                            "description": "Discord server ID (Guild ID) to list channels from",
                        },
                    },
                    "required": [
                        "guild_id"
                    ],
                },
            ),
            Tool(
                name="fetch_server_with_channels",
                description="Get a server by its ID",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "string",
                            "description": "Discord server ID to fetch",
                        },
                    },
                    "required": ["guild_id"],
                },
            ),
            Tool(
                name="fetch_channel_details",
                description="Fetch a channel by its ID and return its details",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Discord channel ID to fetch",
                        },
                    },
                    "required": ["channel_id"],
                },
            ),
            Tool(
                name="read_messages_from_channel",
                description="Read recent messages from a channel with filtering options",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Discord channel ID from which to fetch messages",
                        },
                        "filter": {
                            "type": "object",
                            "description": "Filtering options for message retrieval",
                            "properties": {
                                "limit": {
                                    "type": "number",
                                    "description": "Number of messages to fetch (max 500)",
                                    "minimum": 1,
                                    "maximum": 500,
                                    "default": 10
                                },
                                "before": {
                                    "type": "string",
                                    "description": "ISO timestamp - retrieve messages before this time (YYYY-MM-DDTHH:MM:SS.sssZ)",
                                },
                                "after": {
                                    "type": "string", 
                                    "description": "ISO timestamp - retrieve messages after this time (YYYY-MM-DDTHH:MM:SS.sssZ)",
                                },
                                "oldest_first": {
                                    "type": "boolean",
                                    "description": "If true, return messages in oldest to newest order. If false, newest to oldest.",
                                    "default": False
                                }
                            },
                            "additionalProperties": False
                        },
                    },
                    "required": ["channel_id", "filter"],
                },
            ),
            Tool(
                name="get_pinned_messages",
                description="Get all pinned messages from a channel (key announcements and important messages)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "Discord channel ID to fetch pinned messages from",
                        },
                    },
                    "required": ["channel_id"],
                },
            ),
            Tool(
                name="get_thread_details",
                description="Analyze a thread's activity (thick threads are hot topics)",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "thread_id": {
                            "type": "string",
                            "description": "Discord thread ID to analyze",
                        },
                        "include_recent_messages": {
                            "type": "boolean",
                            "description": "Include recent messages from the thread",
                            "default": True
                        },
                        "recent_limit": {
                            "type": "number",
                            "description": "Number of recent messages to include (max 10)",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        }
                    },
                    "required": ["thread_id"],
                },
            ),
            Tool(
                name="get_workspace_structure",
                description="Get raw workspace structural data with all channels, threads, and working groups",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "guild_id": {
                            "type": "string",
                            "description": "Discord server ID to analyze",
                        },
                    },
                    "required": ["guild_id"],
                },
            ),
        ]

    @app.call_tool()
    @require_discord_client
    async def call_tool(name: str, arguments: Any) -> List[TextContent]:
        """
        Main tool dispatcher that routes calls to specific handler methods.
        """
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        
        # Tool dispatch mapping
        tool_handlers = {
            "get_all_channels_across_servers": handle_get_all_channels_across_servers,
            "fetch_server_with_channels": handle_fetch_server_with_channels,
            "fetch_channel_details": handle_fetch_channel_details,
            "read_messages_from_channel": handle_read_messages_from_channel,
            "get_pinned_messages": handle_get_pinned_messages,
            "get_thread_details": handle_get_thread_details,
            "get_workspace_structure": handle_get_workspace_structure,
        }
        
        if name not in tool_handlers:
            raise ValueError(f"Unknown tool: {name}")
        
        try:
            return await tool_handlers[name](arguments)
        except Exception as e:
            logger.error(f"Error executing tool {name}: {str(e)}")
            return [
                TextContent(
                    type="text",
                    text=f"Error executing tool {name}: {str(e)}"
                )
            ] 