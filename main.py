
from discord_agent.prompts.thread_discussion import get_prompt
from .common.agent_tester import MultiAgentTester
import asyncio
from dotenv import load_dotenv
# Load environment variables
load_dotenv()

MCP_SERVER_CHANNEL_ID = "1358869848138059966"

# from .agent.agent import root_agent
# tester = MultiAgentTester(root_agent)
# prompt = """list all channels in the server 1338823128947757149 and read 100 messages from each channel in the server. Group the messages by channel and thread."""

# from .agent.workspace_understanding_agent import workspace_understanding_agent
# tester = MultiAgentTester(workspace_understanding_agent)
# prompt = f"""Help me understand the workspace structure in the channel {MCP_SERVER_CHANNEL_ID}."""

from .agent.agent import root_agent
tester = MultiAgentTester(root_agent)
prompt = get_prompt("https://discord.com/channels/1358869848138059966/1399415703760797747")

async def main():
    await tester.run_agent(prompt)

if __name__ == "__main__":
    asyncio.run(main())