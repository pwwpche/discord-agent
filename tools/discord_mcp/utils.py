"""
Utility functions for Discord MCP server.
Contains common functionality for channel processing, message formatting, and decorators.
"""

import logging
from typing import Any, List, Dict, Optional
from functools import wraps

import discord

logger = logging.getLogger("discord-mcp-server")

def format_reactions(reactions: List[dict]) -> str:
    """
    Format a list of reaction dictionaries into a human-readable string.
    Each reaction is shown as: emoji(count).
    If no reactions are present, returns "No reactions".
    """
    if not reactions:
        return "No reactions"
    return ", ".join(f"{r['emoji']}({r['count']})" for r in reactions)


def create_channel_dict(channel: discord.abc.GuildChannel) -> Dict[str, Any]:
    """
    Create a standardized dictionary representation of a Discord channel.
    Handles different channel types and their specific attributes.
    """
    channel_obj = {
        "id": channel.id,
        "name": channel.name,
        "type": str(channel.type),
        "position": getattr(channel, 'position', None),
        "category_id": getattr(channel, 'category_id', None),
        "guild_id": channel.guild.id,
    }
    
    # Add threads only for text channels
    if isinstance(channel, discord.TextChannel):
        channel_obj["threads"] = []
        logger.info(f"Found {len(channel.threads)} active threads for channel {channel.name}")
        for thread in channel.threads:
            thread_obj = {
                "id": thread.id,
                "name": thread.name,
                "type": str(thread.type),
                "category_id": getattr(thread, 'category_id', None),
            }
            channel_obj["threads"].append(thread_obj)
    
    return channel_obj


def process_message_reactions(message: discord.Message) -> List[Dict[str, Any]]:
    """
    Process and format message reactions into a standardized format.
    """
    reaction_data = []
    for reaction in message.reactions:
        if isinstance(reaction.emoji, str):
            emoji_str = reaction.emoji
        elif hasattr(reaction.emoji, 'name') and reaction.emoji.name:
            emoji_str = str(reaction.emoji.name)
        elif hasattr(reaction.emoji, 'id'):
            emoji_str = str(reaction.emoji.id)
        else:
            emoji_str = str(reaction.emoji)
        
        reaction_info = {"emoji": emoji_str, "count": reaction.count}
        logger.debug(f"Found reaction: {emoji_str}")
        reaction_data.append(reaction_info)
    
    return reaction_data


def require_discord_client(func):
    """
    Decorator to ensure the Discord client is ready before executing a tool.
    Raises a RuntimeError if the client is not yet available.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        from .bot import get_discord_client
        client = get_discord_client()
        if not client:
            raise RuntimeError("Discord client not ready")
        return await func(*args, **kwargs)
    return wrapper


def is_messageable_channel(channel: Any) -> bool:
    """
    Check if a channel supports message history.
    Returns True for channels that have a history method.
    """
    return isinstance(channel, (discord.TextChannel, discord.VoiceChannel, discord.Thread, discord.DMChannel)) 