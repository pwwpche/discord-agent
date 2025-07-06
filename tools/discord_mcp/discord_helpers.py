"""
Discord Helper Classes and Functions

This module contains reusable helper classes and functions to simplify
Discord operations and reduce code duplication in handlers.
"""

import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime

import discord
from mcp.types import TextContent

from .bot import get_discord_client
from .utils import process_message_reactions, format_reactions, is_messageable_channel

logger = logging.getLogger("discord-mcp-server")


class DiscordClientManager:
    """Manages Discord client operations and validation."""
    
    @staticmethod
    def get_client() -> discord.Client:
        """Get the Discord client, raising an error if not ready."""
        client = get_discord_client()
        if not client:
            raise RuntimeError("Discord client not ready")
        return client
    
    @staticmethod
    async def fetch_channel(channel_id: Union[str, int]) -> Any:
        """Fetch a channel by ID with error handling."""
        client = DiscordClientManager.get_client()
        try:
            return await client.fetch_channel(int(channel_id))
        except discord.NotFound:
            raise ValueError(f"Channel {channel_id} not found")
        except discord.Forbidden:
            raise PermissionError(f"No permission to access channel {channel_id}")
    
    @staticmethod
    async def fetch_guild(guild_id: Union[str, int]) -> discord.Guild:
        """Fetch a guild by ID with error handling."""
        client = DiscordClientManager.get_client()
        try:
            return await client.fetch_guild(int(guild_id))
        except discord.NotFound:
            raise ValueError(f"Server {guild_id} not found")
        except discord.Forbidden:
            raise PermissionError(f"No permission to access server {guild_id}")


class ChannelValidator:
    """Validates channel types and capabilities."""
    
    @staticmethod
    def supports_message_history(channel) -> bool:
        """Check if channel supports message history."""
        return is_messageable_channel(channel)
    
    @staticmethod
    def supports_pinned_messages(channel) -> bool:
        """Check if channel supports pinned messages."""
        return isinstance(channel, (discord.TextChannel, discord.DMChannel, discord.Thread))
    
    @staticmethod
    def is_thread(channel) -> bool:
        """Check if channel is a thread."""
        return isinstance(channel, discord.Thread)
    
    @staticmethod
    def is_text_channel(channel) -> bool:
        """Check if channel is a text channel."""
        return isinstance(channel, discord.TextChannel)


class TimestampParser:
    """Handles timestamp parsing operations."""
    
    @staticmethod
    def parse(timestamp_str: str) -> Optional[datetime]:
        """Parse an ISO timestamp string to a datetime object."""
        if not timestamp_str:
            return None
        
        try:
            # Try parsing with microseconds and timezone
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            
            # Handle different timestamp formats
            formats = [
                "%Y-%m-%dT%H:%M:%S.%f%z",  # With microseconds and timezone
                "%Y-%m-%dT%H:%M:%S%z",     # Without microseconds but with timezone
                "%Y-%m-%dT%H:%M:%S.%f",    # With microseconds but no timezone
                "%Y-%m-%dT%H:%M:%S",       # Basic format
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(timestamp_str, fmt)
                except ValueError:
                    continue
            
            # If none of the formats work, try fromisoformat (Python 3.7+)
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            
        except Exception as e:
            logger.error(f"Failed to parse timestamp '{timestamp_str}': {e}")
            return None


class FilterProcessor:
    """Processes filter parameters for various Discord operations."""
    
    @staticmethod
    def process_message_filter(filter_params: Dict[str, Any]) -> Dict[str, Any]:
        """Process filter parameters for message history operations."""
        history_kwargs: Dict[str, Any] = {
            "limit": min(int(filter_params.get("limit", 10)), 500),  # Cap at 500 messages
        }
        
        if "oldest_first" in filter_params:
            history_kwargs["oldest_first"] = filter_params["oldest_first"]
        
        # Parse timestamps if provided
        if "before" in filter_params:
            before = TimestampParser.parse(filter_params["before"])
            if before is None:
                raise ValueError("Invalid 'before' timestamp format. Use ISO format: YYYY-MM-DDTHH:MM:SS.sssZ")
            history_kwargs["before"] = before
        
        if "after" in filter_params:
            after = TimestampParser.parse(filter_params["after"])
            if after is None:
                raise ValueError("Invalid 'after' timestamp format. Use ISO format: YYYY-MM-DDTHH:MM:SS.sssZ")
            history_kwargs["after"] = after
        
        return history_kwargs
    
    @staticmethod
    def process_reaction_filter(filter_params: Dict[str, Any]) -> Dict[str, Any]:
        """Process filter parameters for reaction-based message searches."""
        result = {
            "min_reactions": filter_params.get("min_reactions", 5),
            "min_reaction_types": filter_params.get("min_reaction_types", 2),
            "target_emojis": filter_params.get("target_emojis", ["👍", "🔥", "✨", "❤️", "💯"]),
            "limit": min(int(filter_params.get("limit", 50)), 500),
            "before": None,
            "after": None,
        }
        
        # Handle timestamp parsing with None check
        if "before" in filter_params and filter_params["before"] is not None:
            result["before"] = TimestampParser.parse(filter_params["before"])
        if "after" in filter_params and filter_params["after"] is not None:
            result["after"] = TimestampParser.parse(filter_params["after"])
            
        return result


class MessageFormatter:
    """Formats Discord messages and related data for output."""
    
    @staticmethod
    def format_message_list(messages: List[Dict[str, Any]], include_reactions: bool = True) -> str:
        """Format a list of messages for output."""
        if not messages:
            return "No messages found."
        
        formatted_messages = []
        for msg in messages:
            formatted = f"{msg['author']} ({msg['timestamp']}): {msg['content']}"
            if include_reactions and msg.get('reactions'):
                formatted += f"\nReactions: {format_reactions(msg['reactions'])}"
            if msg.get('jump_url'):
                formatted += f"\nJump URL: {msg['jump_url']}"
            formatted_messages.append(formatted)
        
        return "\n\n".join(formatted_messages)
    
    @staticmethod
    def format_pinned_messages(messages: List[Dict[str, Any]]) -> str:
        """Format pinned messages with special formatting."""
        if not messages:
            return "No pinned messages found."
        
        formatted_messages = []
        for msg in messages:
            formatted = f"📌 {msg['author']} ({msg['timestamp']}): {msg['content']}"
            formatted += f"\nReactions: {format_reactions(msg['reactions'])}"
            formatted += f"\nJump URL: {msg['jump_url']}"
            formatted_messages.append(formatted)
        
        return "\n\n".join(formatted_messages)
    
    @staticmethod
    def format_hot_messages(messages: List[Dict[str, Any]], limit: int = 10) -> str:
        """Format highly reacted messages with engagement metrics."""
        if not messages:
            return "No highly reacted messages found."
        
        formatted_messages = []
        for msg in messages[:limit]:
            content_preview = msg['content'][:200] + ("..." if len(msg['content']) > 200 else "")
            formatted = (
                f"🔥 {msg['author']} ({msg['timestamp']}) - "
                f"{msg['total_reactions']} reactions ({msg['reaction_types']} types):\n"
                f"{content_preview}\n"
                f"Reactions: {format_reactions(msg['reactions'])}\n"
                f"Jump URL: {msg['jump_url']}"
            )
            formatted_messages.append(formatted)
        
        return "\n\n".join(formatted_messages)
    
    @staticmethod
    def format_channel_list(channels: List[Dict[str, Any]]) -> str:
        """Format a list of channels for output."""
        if not channels:
            return "No channels found."
        
        formatted_channels = []
        for ch in channels:
            formatted = (
                f"📢 {ch['name']} (ID: {ch['id']}) - {ch['type']}\n"
                f"   Topic: {ch.get('topic') or 'No topic'}\n"
                f"   Category: {ch.get('category') or 'None'}\n"
                f"   Recent Activity: {ch.get('recent_activity', 0)} messages"
            )
            formatted_channels.append(formatted)
        
        return "\n\n".join(formatted_channels)
    
    @staticmethod
    def format_workspace_overview(workspace_structure: Dict[str, Any]) -> str:
        """Format comprehensive workspace structure overview."""
        overview = f"🏢 **{workspace_structure['guild_info']['name']}** Workspace Overview\n"
        overview += f"📊 {workspace_structure['total_channels']} channels, {workspace_structure['total_threads']} threads\n\n"
        
        # Format by categories
        for category_name, category_data in workspace_structure["categories"].items():
            overview += f"📁 **{category_name}** ({len(category_data['channels'])} channels, {category_data['total_threads']} threads)\n"
            
            for channel in category_data["channels"]:
                thread_info = f" ({len(channel['threads'])} threads)" if channel['threads'] else ""
                activity_info = f" - {channel['recent_activity']} recent msgs" if channel['recent_activity'] > 0 else ""
                overview += f"   #{channel['name']}{thread_info}{activity_info}\n"
                
                # Show thread names for channels with threads
                if channel['threads']:
                    for thread in channel['threads'][:3]:  # Show first 3 threads
                        overview += f"     🧵 {thread['name']} ({thread['message_count']} msgs)\n"
                    if len(channel['threads']) > 3:
                        overview += f"     ... and {len(channel['threads']) - 3} more threads\n"
            overview += "\n"
        
        return overview
    
    @staticmethod
    def format_working_groups(working_groups: List[Dict[str, Any]]) -> str:
        """Format working groups and active projects."""
        if not working_groups:
            return "No working groups or active projects found."
        
        formatted = "🏗️ **Working Groups & Active Projects**\n\n"
        
        for wg in working_groups:
            type_emoji = "👥" if wg["type"] == "working_group" else "🚀"
            formatted += f"{type_emoji} **#{wg['channel_name']}** ({wg['category']})\n"
            formatted += f"   📊 {wg['thread_count']} threads, {wg['recent_activity']} recent messages\n"
            
            if wg['threads']:
                formatted += "   📋 Active Threads:\n"
                for thread in wg['threads']:
                    status = "📦 Archived" if thread.get('archived') else "🟢 Active"
                    formatted += f"      • {thread['name']} ({thread['message_count']} msgs) {status}\n"
            formatted += "\n"
        
        return formatted
    
    @staticmethod
    def format_filter_summary(history_kwargs: Dict[str, Any]) -> str:
        """Format filter parameters for logging/output."""
        filter_summary = []
        for k, v in history_kwargs.items():
            if isinstance(v, datetime):
                filter_summary.append(f"{k}={v.isoformat()}")
            else:
                filter_summary.append(f"{k}={v}")
        return ", ".join(filter_summary)


class MessageCollector:
    """Collects and processes messages from Discord channels."""
    
    @staticmethod
    async def collect_messages(channel, history_kwargs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect messages from a channel with the given parameters."""
        messages = []
        
        if not ChannelValidator.supports_message_history(channel):
            raise ValueError(f"Channel type {type(channel).__name__} does not support message history")
        
        async for message in channel.history(**history_kwargs):
            reaction_data = process_message_reactions(message)
            messages.append({
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "reactions": reaction_data,
                "jump_url": message.jump_url
            })
        
        return messages
    
    @staticmethod
    async def collect_pinned_messages(channel) -> List[Dict[str, Any]]:
        """Collect all pinned messages from a channel."""
        if not ChannelValidator.supports_pinned_messages(channel):
            raise ValueError(f"Channel type {type(channel).__name__} does not support pinned messages")
        
        pinned_messages = await channel.pins()
        messages = []
        
        for message in pinned_messages:
            reaction_data = process_message_reactions(message)
            messages.append({
                "id": str(message.id),
                "author": str(message.author),
                "content": message.content,
                "timestamp": message.created_at.isoformat(),
                "reactions": reaction_data,
                "jump_url": message.jump_url
            })
        
        return messages
    
    @staticmethod
    def filter_hot_messages(messages: List[Dict[str, Any]], filter_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter messages based on reaction criteria."""
        hot_messages = []
        
        for message_data in messages:
            if not message_data.get('reactions'):
                continue
            
            reactions = message_data['reactions']
            total_reactions = sum(r["count"] for r in reactions)
            reaction_types = len(reactions)
            
            # Check if message meets criteria
            has_target_emoji = any(
                emoji in str(r['emoji']) 
                for r in reactions 
                for emoji in filter_criteria['target_emojis']
            )
            
            if (total_reactions >= filter_criteria['min_reactions'] or 
                reaction_types >= filter_criteria['min_reaction_types'] or 
                has_target_emoji):
                
                message_data.update({
                    "total_reactions": total_reactions,
                    "reaction_types": reaction_types,
                    "has_target_emoji": has_target_emoji
                })
                hot_messages.append(message_data)
        
        # Sort by total reactions descending
        hot_messages.sort(key=lambda x: x["total_reactions"], reverse=True)
        return hot_messages


class WorkspaceAnalyzer:
    """Analyzes Discord workspace structure and activity for topic understanding."""
    
    @staticmethod
    async def get_comprehensive_workspace_structure(guild) -> Dict[str, Any]:
        """Get comprehensive workspace structure with channels, threads, and activity metrics."""
        channels = await guild.fetch_channels()
        
        workspace_structure = {
            "guild_info": {
                "id": guild.id,
                "name": guild.name,
                "member_count": guild.member_count if hasattr(guild, 'member_count') and guild.member_count is not None else 0
            },
            "categories": {},
            "channels": [],
            "total_channels": 0,
            "total_threads": 0
        }
        
        for channel in channels:
            if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                continue
            
            # Get category info
            category_name = str(channel.category) if channel.category else "No Category"
            if category_name not in workspace_structure["categories"]:
                workspace_structure["categories"][category_name] = {
                    "channels": [],
                    "total_threads": 0
                }
            
            # Build channel info
            channel_info = {
                "id": channel.id,
                "name": channel.name,
                "type": str(channel.type),
                "category": category_name,
                "position": channel.position,
                "topic": getattr(channel, 'topic', None),
                "threads": [],
                "recent_activity": 0
            }
            
            # Get thread information for text channels
            if isinstance(channel, discord.TextChannel):
                try:
                    # Get active threads
                    for thread in channel.threads:
                        thread_info = {
                            "id": thread.id,
                            "name": thread.name,
                            "message_count": thread.message_count or 0,
                            "member_count": thread.member_count or 0,
                            "archived": thread.archived,
                            "created_at": thread.created_at.isoformat() if thread.created_at else None
                        }
                        channel_info["threads"].append(thread_info)
                        workspace_structure["total_threads"] += 1
                        workspace_structure["categories"][category_name]["total_threads"] += 1
                    
                    # Get recent activity count
                    if ChannelValidator.supports_message_history(channel):
                        recent_count = 0
                        async for message in channel.history(limit=10):
                            recent_count += 1
                        channel_info["recent_activity"] = recent_count
                except:
                    pass
            
            workspace_structure["categories"][category_name]["channels"].append(channel_info)
            workspace_structure["channels"].append(channel_info)
            workspace_structure["total_channels"] += 1
        
        return workspace_structure
    
    @staticmethod
    def identify_working_groups(workspace_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify working groups and project channels from workspace structure."""
        working_groups = []
        
        # Common working group patterns
        wg_patterns = ["wg-", "working-group", "team-", "project-", "dev-", "design-"]
        
        for channel in workspace_structure["channels"]:
            channel_name_lower = channel["name"].lower()
            
            # Check if channel matches working group patterns
            is_working_group = any(pattern in channel_name_lower for pattern in wg_patterns)
            
            # Also consider channels with many threads as potential working groups
            has_significant_threads = len(channel["threads"]) >= 3
            
            if is_working_group or has_significant_threads:
                wg_info = {
                    "channel_id": channel["id"],
                    "channel_name": channel["name"],
                    "category": channel["category"],
                    "thread_count": len(channel["threads"]),
                    "recent_activity": channel["recent_activity"],
                    "type": "working_group" if is_working_group else "active_project",
                    "threads": channel["threads"][:5]  # Top 5 threads for preview
                }
                working_groups.append(wg_info)
        
        # Sort by activity and thread count
        working_groups.sort(key=lambda x: (x["recent_activity"], x["thread_count"]), reverse=True)
        return working_groups


class ResponseBuilder:
    """Builds standardized MCP responses."""
    
    @staticmethod
    def success(text: str) -> List[TextContent]:
        """Create a successful response with the given text."""
        return [TextContent(type="text", text=text)]
    
    @staticmethod
    def error(error_msg: str) -> List[TextContent]:
        """Create an error response with the given message."""
        return [TextContent(type="text", text=f"Error: {error_msg}")]
    
    @staticmethod
    def handle_discord_errors(func):
        """Decorator to handle common Discord API errors."""
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                return ResponseBuilder.error(str(e))
            except PermissionError as e:
                return ResponseBuilder.error(str(e))
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                return ResponseBuilder.error(f"Unexpected error: {str(e)}")
        return wrapper 