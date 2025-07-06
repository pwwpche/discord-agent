"""
Discord bot setup and event handlers.
Manages the Discord client lifecycle and provides access to the bot instance.
"""

import os
import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands
from dotenv import load_dotenv

logger = logging.getLogger("discord-mcp-server")

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Configure Discord bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Global variable to store the Discord client instance once the bot is ready
_discord_client: Optional[commands.Bot] = None


def get_discord_client() -> Optional[commands.Bot]:
    """
    Get the Discord client instance.
    Returns None if the client is not yet ready.
    """
    return _discord_client


def get_discord_token() -> str:
    """
    Get the Discord token, ensuring it's available.
    """
    if not DISCORD_TOKEN:
        raise ValueError("DISCORD_TOKEN environment variable is required")
    return DISCORD_TOKEN


@bot.event
async def on_ready():
    """
    Event handler called when the Discord bot successfully logs in.
    Sets the global discord_client variable and logs the bot's username.
    """
    global _discord_client
    _discord_client = bot
    
    # Wait until the bot user is fully loaded
    while True:
        if bot.user is not None:
            break
        await asyncio.sleep(0.1)
    
    logger.info(f"Logged in as {bot.user.name}")


async def start_bot():
    """
    Start the Discord bot.
    This function starts the bot and returns a task.
    """
    return asyncio.create_task(bot.start(get_discord_token())) 