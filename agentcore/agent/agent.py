from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from mcp.client.streamable_http import streamablehttp_client
from strands import Agent
from strands.tools.mcp.mcp_client import MCPClient
import logging

logger = logging.getLogger("bedrock_agentcore.app")

app = BedrockAgentCoreApp()

@app.entrypoint
def invoke(payload):
    """Your AI agent function"""

    user_message = payload.get("prompt", "Hello! How can I help you today?")
    system_message = payload.get("system_prompt", "")
    doc_tools_enabled = payload.get("doc_tools_enabled", False)
    model = payload.get("model")
    if model is None or model == "":
        #model =  "anthropic.claude-3-5-sonnet-20240620-v1:0"
        # need the us prefix, per https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/amazon-bedrock/#on-demand-throughput-isnt-supported
        model =  "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    logger.error("model: " + str(model))

    # default to no tools
    agent = Agent(system_prompt=system_message, model=model)

    if doc_tools_enabled:
        streamable_http_mcp_client = MCPClient(lambda: streamablehttp_client("https://mcp.context7.com/mcp"))

        # Create an agent with MCP tools
        with streamable_http_mcp_client:
            # Get the tools from the MCP server
            tools = streamable_http_mcp_client.list_tools_sync()
    
            agent = Agent(system_prompt=system_message, tools=tools, model=model)

    result = agent(user_message)
    return {"result": result.message}

if __name__ == "__main__":
    app.run()
