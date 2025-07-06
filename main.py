
from .common.agent_tester import MultiAgentTester
import asyncio

MCP_SERVER_CHANNEL_ID = "1390025984849219705"

# from .agent.agent import root_agent
# tester = MultiAgentTester(root_agent)
# prompt = """list all channels in the server 1390025984849219705 and read 100 messages from each channel in the server. Group the messages by channel and thread."""

from .agent.workspace_understanding_agent import workspace_understanding_agent
tester = MultiAgentTester(workspace_understanding_agent)
prompt = f"""Help me understand the workspace structure and activity in the server {MCP_SERVER_CHANNEL_ID}?"""

async def main():
    await tester.run_agent(prompt)

if __name__ == "__main__":
    asyncio.run(main())