import os
import ssl
import urllib3
import logging
import json

from strands import Agent
from strands.models import BedrockModel

from flight_agent import run_flight_agent
from weather_agent import run_weather_agent
from accommodation_agent import run_accommodation_agent

from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

# Disable SSL (Hackathon mode)
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['AWS_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.getLogger().setLevel(logging.ERROR)

# Load Gateway Config
with open('../gateway/gateway_config.json', 'r') as f:
    config = json.load(f)

# Create Gateway Client
client = GatewayClient(region_name="us-east-1")

access_token = client.get_access_token_for_cognito(
    config['cognito_info']['client_info']
)

# MCP Transport
transport = streamablehttp_client(
    config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}"
    }
)

# MCP Client
mcp_client = MCPClient(lambda: transport)
mcp_client.__enter__()

# Load MCP Tools
tools = mcp_client.list_tools_sync()

pdf_tool = next(
    tool for tool in tools
    if "generate_travel_pdf" in tool.tool_name.lower()
)

# Bedrock Model
model = BedrockModel(
    model_id="openai.gpt-oss-safeguard-120b",
    temperature=0.3,
    streaming=False,
    region_name="us-east-1"
)

# Supervisor Agent
supervisor_agent = Agent(
    model=model,
    system_prompt="""
You are a supervisor travel assistant.

Responsibilities:
- Understand user intent
- Decide whether flight, weather, or accommodation agent is needed
- Combine responses cleanly

Rules:
- Never show internal reasoning
- Never repeat responses
- Keep output clean and structured
- If no tool needed, answer directly
"""
)

print("\nSupervisor Agent Ready")
print("Type 'exit' or 'quit' to stop")

# Keywords
flight_keywords = ["flight", "ticket", "book", "travel", "fly"]
weather_keywords = ["weather", "forecast", "temperature", "rain"]
hotel_keywords = ["hotel", "stay", "accommodation", "room"]

while True:

    query = input("\nYou: ")

    if query.lower() in ["exit", "quit"]:
        break

    try:

        flight_response = ""
        weather_response = ""
        hotel_response = ""

        is_flight = any(word in query.lower() for word in flight_keywords)
        is_weather = any(word in query.lower() for word in weather_keywords)
        is_hotel = any(word in query.lower() for word in hotel_keywords)

        if is_flight:
            print("\nFlight Agent Working...\n")

            flight_query = f"""
Extract flight details and return only flight results.

User request:
{query}
"""
            flight_response = run_flight_agent(flight_query)

        if is_weather:
            print("\nWeather Agent Working...\n")

            weather_query = f"""
Extract weather request and return forecast.

User request:
{query}
"""
            weather_response = run_weather_agent(weather_query)

        if is_hotel:
            print("\nAccommodation Agent Working...\n")

            hotel_query = f"""
Extract hotel request and return accommodation options.

User request:
{query}
"""
            hotel_response = run_accommodation_agent(hotel_query)

        if flight_response or weather_response or hotel_response:

            print("\nFINAL RESPONSE\n")

            if flight_response:
                print("\nFlights:\n")
                print(flight_response.strip())

            if weather_response:
                print("\nWeather:\n")
                print(weather_response.strip())

            if hotel_response:
                print("\nHotels:\n")
                print(hotel_response.strip())

            generate_pdf = input("\nGenerate PDF report? (yes/no): ")

            if generate_pdf.lower() == "yes":

                print("\nGenerating PDF...\n")

                pdf_payload = {
                    "flight_details": str(flight_response),
                    "weather_details": str(weather_response),
                    "hotel_details": str(hotel_response)
                }

                pdf_result = mcp_client.call_tool_sync(
                    "generate-pdf",
                    pdf_tool.tool_name,
                    pdf_payload
                )

                print("\nPDF Generated:\n")

                response_text = pdf_result["content"][0]["text"]

                response_json = json.loads(response_text)
                body_json = json.loads(response_json["body"])

                pdf_url = body_json["pdf_url"]

                print("\nPDF URL:\n")
                print(pdf_url)

        else:
            print("\nSupervisor Response:\n")

            response = supervisor_agent(query)
            print(str(response).strip())

    except Exception as e:
        print(f"\nError: {e}")