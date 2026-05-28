import os
import ssl
import urllib3
import logging
import json

from strands import Agent
from strands.models import BedrockModel

from flight_agent import run_flight_agent
from weather_agent import run_weather_agent

from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

# Disable SSL (Hackathon mode)

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['AWS_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

ssl._create_default_https_context = ssl._create_unverified_context

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

# Reduce noisy logs

logging.getLogger().setLevel(logging.ERROR)

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

# Create MCP Client

mcp_client = MCPClient(lambda: transport)

mcp_client.__enter__()

# Load MCP Tools

tools = mcp_client.list_tools_sync()

# Get PDF Tool

pdf_tool = next(
    tool for tool in tools
    if "generate_travel_pdf"
    in tool.tool_name.lower()
)

# Create Bedrock Model

model = BedrockModel(
    model_id="openai.gpt-oss-safeguard-120b",
    temperature=0.3,
    streaming=False,
    region_name="us-east-1"
)

# Create Supervisor Agent

supervisor_agent = Agent(

    model=model,

    system_prompt="""
You are a supervisor travel assistant.

Responsibilities:
- Understand user intent
- Decide whether flight or weather agent is needed
- Combine responses cleanly

Rules:
- Never show internal reasoning
- Never repeat responses
- Keep output clean and structured
- If no tool needed, answer directly
"""
)

print("\n✅ Supervisor Agent Ready")
print("Type 'exit' or 'quit' to stop")

# Keywords

flight_keywords = [
    "flight",
    "ticket",
    "book",
    "travel",
    "fly"
]

weather_keywords = [
    "weather",
    "forecast",
    "temperature",
    "rain"
]

while True:

    query = input("\nYou: ")

    if query.lower() in ["exit", "quit"]:
        break

    try:

        flight_response = ""
        weather_response = ""

        is_flight = any(
            word in query.lower()
            for word in flight_keywords
        )

        is_weather = any(
            word in query.lower()
            for word in weather_keywords
        )

        # Flight Agent

        if is_flight:

            print("\n✈️ Flight Agent Working...\n")

            flight_query = f"""
Extract flight details and return only flight results.

User request:
{query}
"""

            flight_response = run_flight_agent(
                flight_query
            )

        # Weather Agent

        if is_weather:

            print("\n🌦️ Weather Agent Working...\n")

            weather_query = f"""
Extract weather request and return forecast.

User request:
{query}
"""

            weather_response = run_weather_agent(
                weather_query
            )

        # Final Combined Output

        if flight_response or weather_response:

            print(
                "\n================ FINAL RESPONSE ================\n"
            )

            if flight_response:

                print("✈️ Flights:\n")

                print(
                    flight_response.strip()
                )

            if weather_response:

                print("\n🌦️ Weather:\n")

                print(
                    weather_response.strip()
                )

            # PDF Generation

            generate_pdf = input(
                "\nGenerate PDF report? (yes/no): "
            )

            if generate_pdf.lower() == "yes":

                print("\n📄 Generating PDF...\n")

                pdf_payload = {

                    "flight_details": str(
                        flight_response
                    ),

                    "weather_details": str(
                        weather_response
                    )
                }

                pdf_result = mcp_client.call_tool_sync(

                    "generate-pdf",

                    pdf_tool.tool_name,

                    pdf_payload
                )

                print("\n📄 PDF Generated:\n")

                response_text = pdf_result[
                    "content"
                ][0]["text"]

                response_json = json.loads(
                    response_text
                )

                body_json = json.loads(
                    response_json["body"]
                )

                pdf_url = body_json["pdf_url"]

                print("\n✅ PDF URL:\n")

                print(pdf_url)

        # Supervisor Handles General Queries

        else:

            print("\n🧠 Supervisor Response:\n")

            response = supervisor_agent(query)

            print(
                str(response).strip()
            )

    except Exception as e:

        print(f"\n❌ Error: {e}")