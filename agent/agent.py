from google.adk.agents import LlmAgent as Agent
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp.client.stdio import StdioServerParameters
from .hot_topic_agent import hot_topic_agent
from .workspace_understanding_agent import workspace_understanding_agent

root_agent = Agent(
    # model="gemini-2.5-pro-preview-06-05",
    model="gemini-2.5-flash",
    name="root_agent",
    description="A root agent that can read Discord channels and messages",
    instruction="""
        You are a root agent that can read Discord channels and messages in them.
    """,
    tools=[
        MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python3",
                    args=["-m", "discord_agent.tools.discord_mcp.server"],
                ),
                timeout=120,
            )
        )
    ],
    sub_agents=[
        hot_topic_agent,
        workspace_understanding_agent
    ],
)
