from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

import json
import os
import ssl
import urllib3
import botocore.httpsession



os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['AWS_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load Gateway Config


with open('../gateway/gateway_config.json', 'r') as f:
    config = json.load(f)

# Create Gateway Client


client = GatewayClient(region_name="us-east-1")

# Get Cognito Access Token


access_token = client.get_access_token_for_cognito(
    config['cognito_info']['client_info']
)

# Create MCP Transport


transport = streamablehttp_client(
    config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}"
    }
)

# Create Bedrock Model


model = BedrockModel(
    model_id="openai.gpt-oss-safeguard-120b",
    temperature=0.3,
    streaming=False,
    region_name="us-east-1"   
)

# Create MCP Client


mcp_client = MCPClient(lambda: transport)

# Start MCP Session


mcp_client.__enter__()
# Load Tools

tools = mcp_client.list_tools_sync()

weather_tools = [
    tool for tool in tools
    if "weather" in tool.tool_name.lower()
]

# Create Weather Agent

weather_agent = Agent(
    name="weather_agent",

    model=model,

    tools=weather_tools,

    system_prompt="""

You are a weather assistant.

Your role is to provide clean, summarized weather forecasts.

Rules:
- Use the tool to get weather data
- DO NOT return raw hourly data
- Summarize weather by day
- Include:
  • Date
  • Temperature range (min–max)
  • General condition (clear, cloudy, etc.)
- Add a short overall summary at the end

Output format example:

Weather in <city> (<dates>):

• <date>: <summary>, temperature between X°C – Y°C  
• <date>: <summary>, temperature between X°C – Y°C  

Overall:
<short advice like "Hot weather expected">

Important:
- Do NOT include thinking text
- Do NOT show raw timestamps
- Keep response concise and user-friendly


"""
)

# Callable Function


def run_weather_agent(query):

    response = weather_agent(query)

    return str(response)

# Standalone Chat Mode


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