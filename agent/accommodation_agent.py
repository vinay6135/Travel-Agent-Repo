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
 
# MCP Client
mcp_client = MCPClient(lambda: transport)
mcp_client.__enter__()
 
# Load tools
tools = mcp_client.list_tools_sync()
 
# Filter accommodation tools
accommodation_tools = [
    tool for tool in tools
    if "accommodation" in tool.tool_name.lower()
]
 
# Create Accommodation Agent
accommodation_agent = Agent(
    name="accommodation_agent",
 
    model=model,
 
    tools=accommodation_tools,
 
    system_prompt="""
You are a hotel recommendation assistant.
 
Your role is to present hotel options in a clean and easy-to-read format.
 
Rules:
- Use only tool data
- Show hotel name, price, and rating
- Sort from best rating to lowest
- Do NOT include explanations or extra text
 
Output format:
 
Hotel Options:
 
1. <Hotel Name>
   Price: ₹<amount>
   Rating: <rating>/5
 
Important:
- Keep formatting clean
- Do not include thinking text
- No extra explanations
"""
)
 
#  Callable Function
def run_accommodation_agent(query):
 
    response = accommodation_agent(query)
 
    return str(response)
 
# Standalone Chat Mode
if __name__ == "__main__":
 
    print("\n===================================")
    print("🏨 Accommodation Agent Ready")
    print("Type 'exit' or 'quit' to stop")
    print("===================================")
 
    while True:
 
        query = input("\nYou: ")
 
        if query.lower() in ["exit", "quit"]:
            break
 
        try:
 
            print("\nAccommodation Agent:", end=" ")
 
            response = run_accommodation_agent(query)
 
            print(response)
 
        except Exception as e:
 
            print(f"\nError: {e}")