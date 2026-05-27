from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

import json

# =====================================
# Load Gateway Config
# =====================================

with open('../gateway/gateway_config.json', 'r') as f:
    config = json.load(f)

# =====================================
# Create Gateway Client
# =====================================

client = GatewayClient(region_name="us-east-1")

# =====================================
# Get Cognito Access Token
# =====================================

access_token = client.get_access_token_for_cognito(
    config['cognito_info']['client_info']
)

# =====================================
# Create MCP Transport
# =====================================

transport = streamablehttp_client(
    config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}"
    }
)

# =====================================
# Create Bedrock Model
# =====================================

model = BedrockModel(
    model_id="amazon.nova-lite-v1:0",
    temperature=0.3,
    streaming=True
)

# =====================================
# Create MCP Client
# =====================================

mcp_client = MCPClient(lambda: transport)

# =====================================
# Start MCP Session
# =====================================

mcp_client.__enter__()

# =====================================
# Load Tools
# =====================================

tools = mcp_client.list_tools_sync()

weather_tools = [
    tool for tool in tools
    if "weather" in tool.tool_name.lower()
]

# =====================================
# Create Weather Agent
# =====================================

weather_agent = Agent(

    model=model,

    tools=weather_tools,

    system_prompt="""
You are a specialized weather assistant.

Responsibilities:
- Provide weather forecasts using MCP tools.
- Never invent weather data.
- Explain forecasts clearly and briefly.
- Mention forecast limitations when needed.
"""
)

# =====================================
# Callable Function
# =====================================

def run_weather_agent(query):

    response = weather_agent(query)

    return str(response)

# =====================================
# Standalone Chat Mode
# =====================================

if __name__ == "__main__":

    print("\n===================================")
    print("🌦️ Weather Agent Ready")
    print("Type 'exit' or 'quit' to stop")
    print("===================================")

    while True:

        query = input("\nYou: ")

        if query.lower() in ["exit", "quit"]:
            break

        try:

            print("\nWeather Agent:", end=" ")

            response = run_weather_agent(query)

            print(response)

        except Exception as e:

            print(f"\nError: {e}")