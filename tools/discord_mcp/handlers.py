"""
Tool handler functions for Discord MCP server.
Contains the implementation of all Discord operations exposed as MCP tools.
Simplified using helper classes for better maintainability.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

import discord
from mcp.types import TextContent

from .discord_helpers import (
    DiscordClientManager,
    ChannelValidator,
    FilterProcessor,
    MessageFormatter,
    MessageCollector,
    ResponseBuilder,
    WorkspaceAnalyzer,
)
from .utils import create_channel_dict

logger = logging.getLogger("discord-mcp-server")


@ResponseBuilder.handle_discord_errors
async def handle_get_all_channels_across_servers(arguments: Dict[str, Any]) -> List[TextContent]:
    """Gets all channels across all servers that this bot has access to"""
    client = DiscordClientManager.get_client()
    channels = client.get_all_channels()
    
    channel_list = []
    for channel in channels:
        if isinstance(channel, discord.abc.GuildChannel):
            channel_obj = create_channel_dict(channel)
            channel_list.append(channel_obj)
    
    return ResponseBuilder.success(f"Channels: {channel_list}")


@ResponseBuilder.handle_discord_errors
async def handle_fetch_server_with_channels(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get all channels in a server by server id."""
    guild = await DiscordClientManager.fetch_guild(arguments["guild_id"])
    channels = await guild.fetch_channels()
    
    server_obj = {
        "id": guild.id,
        "name": guild.name,
        "channels": []
    }
    
    for channel in channels:
        if isinstance(channel, discord.abc.GuildChannel):
            channel_obj = create_channel_dict(channel)
            server_obj["channels"].append(channel_obj)
    
    return ResponseBuilder.success(f"Server: {server_obj}")


@ResponseBuilder.handle_discord_errors
async def handle_fetch_channel_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get details of a channel by channel id."""
    channel = await DiscordClientManager.fetch_channel(arguments["channel_id"])
    return ResponseBuilder.success(f"Channel: {channel}")


@ResponseBuilder.handle_discord_errors
async def handle_read_messages_from_channel(arguments: Dict[str, Any]) -> List[TextContent]:
    """Read all messages from a channel by channel id.
    
    Channel can be a thread or a channel.
    Filtering options are available.
    """
    channel = await DiscordClientManager.fetch_channel(arguments["channel_id"])
    
    # Process filter parameters and collect messages
    filter_params = arguments.get("filter", {})
    history_kwargs = FilterProcessor.process_message_filter(filter_params)
    
    logger.info(f"Reading messages with filters: {MessageFormatter.format_filter_summary(history_kwargs)}")
    
    messages = await MessageCollector.collect_messages(channel, history_kwargs)
    formatted_messages = MessageFormatter.format_message_list(messages)
    filter_summary = MessageFormatter.format_filter_summary(history_kwargs)
    
    result_text = f"Retrieved {len(messages)} messages (filters: {filter_summary}):\n\n{formatted_messages}"
    return ResponseBuilder.success(result_text)


@ResponseBuilder.handle_discord_errors
async def handle_get_pinned_messages(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get all pinned messages from a channel by channel id."""
    channel = await DiscordClientManager.fetch_channel(arguments["channel_id"])
    
    messages = await MessageCollector.collect_pinned_messages(channel)
    
    if not messages:
        return ResponseBuilder.success("No pinned messages found in this channel")
    
    formatted_messages = MessageFormatter.format_pinned_messages(messages)
    result_text = f"Found {len(messages)} pinned messages:\n\n{formatted_messages}"
    return ResponseBuilder.success(result_text)


@ResponseBuilder.handle_discord_errors
async def handle_get_thread_details(arguments: Dict[str, Any]) -> List[TextContent]:
    """Get details of a thread by thread id."""
    thread = await DiscordClientManager.fetch_channel(arguments["thread_id"])
    
    if not ChannelValidator.is_thread(thread):
        raise ValueError(f"Channel {arguments['thread_id']} is not a thread")
    
    # Get thread details
    thread_info = {
        "id": thread.id,
        "name": thread.name,
        "parent_channel": str(thread.parent) if thread.parent else None,
        "parent_channel_id": thread.parent_id,
        "owner": str(thread.owner) if thread.owner else None,
        "created_at": thread.created_at.isoformat() if thread.created_at else None,
        "archived": thread.archived,
        "locked": thread.locked,
        "message_count": thread.message_count or 0,
        "member_count": thread.member_count or 0,
    }
    
    # Get the starter message
    starter_message = None
    try:
        starter_msg = await thread.fetch_message(thread.id)
        from .utils import process_message_reactions
        starter_reactions = process_message_reactions(starter_msg)
        starter_message = {
            "content": starter_msg.content,
            "author": str(starter_msg.author),
            "reactions": starter_reactions,
            "timestamp": starter_msg.created_at.isoformat()
        }
    except:
        pass
    
    # Get recent messages if requested
    recent_messages = []
    include_recent = arguments.get("include_recent_messages", True)
    
    if include_recent and thread_info["message_count"] > 1:
        recent_limit = min(arguments.get("recent_limit", 5), 10)
        history_kwargs = {"limit": recent_limit}
        
        try:
            all_recent = await MessageCollector.collect_messages(thread, history_kwargs)
            # Skip starter message
            recent_messages = [msg for msg in all_recent if msg["id"] != str(thread.id)]
            # Truncate content for readability
            for msg in recent_messages:
                if len(msg["content"]) > 200:
                    msg["content"] = msg["content"][:200] + "..."
        except:
            pass
    
    # Format output
    output = f"Thread Analysis: {thread_info['name']}\n"
    output += f"Messages: {thread_info['message_count']} | Members: {thread_info['member_count']}\n"
    output += f"Created: {thread_info['created_at']} | Owner: {thread_info['owner']}\n"
    output += f"Status: {'Archived' if thread_info['archived'] else 'Active'} | {'Locked' if thread_info['locked'] else 'Unlocked'}\n\n"
    
    if starter_message:
        from .utils import format_reactions
        output += f"📝 Starter Message by {starter_message['author']}:\n{starter_message['content']}\n"
        output += f"Reactions: {format_reactions(starter_message['reactions'])}\n\n"
    
    if recent_messages:
        from .utils import format_reactions
        output += f"🔄 Recent Messages ({len(recent_messages)}):\n"
        for msg in recent_messages:
            output += f"{msg['author']}: {msg['content']}\nReactions: {format_reactions(msg['reactions'])}\n\n"
    
    return ResponseBuilder.success(output)


@ResponseBuilder.handle_discord_errors
async def handle_get_workspace_structure(arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle the get_workspace_structure tool call to provide raw workspace structural data."""
    guild = await DiscordClientManager.fetch_guild(arguments["guild_id"])
    
    # Get comprehensive workspace structure - return raw data, not formatted overview
    workspace_structure = await WorkspaceAnalyzer.get_comprehensive_workspace_structure(guild)
    
    # Identify working groups - return raw data
    working_groups = WorkspaceAnalyzer.identify_working_groups(workspace_structure)
    
    # Return structured data instead of formatted text
    result_data = {
        "workspace_structure": workspace_structure,
        "working_groups": working_groups
    }
    
    return ResponseBuilder.success(str(result_data)) 