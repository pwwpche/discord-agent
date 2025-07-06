# Discord Topic Updates Agent 

This agent helps users understand the overall picture and latest updates in a discord server.

It uses a MCP Server to gather the latest messages from a discord guild. It goes into each channel, extracting messages, and then use Gemini(for its large context window) to analyze the topics and updates.

### Project structure:

* **Agents**: `workspace_understanding_agent` for getting a high level understanding of the whole server. `hot_topic_aagent` for understanding hot topics

* **Tools**: Discord related tools for getting guild, channel, threads and messages. All tools are exposed via MCP Server.

### Setup

Follow https://www.speakeasy.com/blog/build-a-mcp-server-tutorial to generate an API key


### Resources:

* Bot DISCORD_TOKEN: https://discord.com/developers/applications/1390023815563837501/bot

* Bot application OAuth: https://discord.com/developers/applications/1390023815563837501/oauth2

### Run

```bash
cd discord_agent/
python3 -m main
```