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


with open('../gateway/gateway_config.json', 'r') as f:
    config = json.load(f)


client = GatewayClient(region_name="us-east-1")

access_token = client.get_access_token_for_cognito(
    config['cognito_info']['client_info']
)

transport = streamablehttp_client(
    config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}"
    }
)

model = BedrockModel(
    model_id="openai.gpt-oss-safeguard-120b",
    temperature=0.3,
    streaming=False,
    region_name="us-east-1"  
)

mcp_client = MCPClient(lambda: transport)

mcp_client.__enter__()

tools = mcp_client.list_tools_sync()

flight_tools = [
    tool for tool in tools
    if "flight" in tool.tool_name.lower()
]

flight_agent = Agent(
    name="flight_agent",

    model=model,

    tools=flight_tools,

    system_prompt="""
You are a flight assistant.

Your role is to present flight options in a clean, structured, and easy-to-read format.

Rules:
- Use only the tool data
- Always include airline name from "airlines" field
- If multiple airlines exist, join with comma
- If airline is missing, show: "Airline: Not specified"

- Keep the output clear and aligned
- Do NOT include explanations, reasoning, or extra text

Output format:

Flight Options:

1. Airline: <airline name>
   Flight Number: <number>

   Outbound:
     Departure at <time> on <date>
     Arrival at <time> on <date>
     Duration: <minutes> minutes
     Stops: <count>

   Return:
     Departure at <time> on <date>
     Arrival at <time> on <date>
     Duration: <minutes> minutes
     Stops: <count>

   Price: $<amount>

Important:
- Maintain spacing and indentation exactly
- Do not include thinking text
- Do not add unrelated information

"""
)

def run_flight_agent(query):

    response = flight_agent(query)

    return str(response)

if __name__ == "__main__":

    print("\n===================================")
    print("✈️ Flight Agent Ready")
    print("Type 'exit' or 'quit' to stop")
    print("===================================")

    while True:

        query = input("\nYou: ")

        if query.lower() in ["exit", "quit"]:
            break

        try:

            print("\nFlight Agent:", end=" ")

            response = run_flight_agent(query)

            print(response)

        except Exception as e:

            print(f"\nError: {e}")