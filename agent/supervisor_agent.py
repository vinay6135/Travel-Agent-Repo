import os
import ssl
import urllib3
import logging
import json
import re
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp.mcp_client import MCPClient
from mcp.client.streamable_http import streamablehttp_client
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
from flight_agent import flight_agent
from weather_agent import weather_agent
from accommodation_agent import accommodation_agent

# Disable SSL

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['AWS_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

ssl._create_default_https_context = (
    ssl._create_unverified_context
)

urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)

logging.getLogger().setLevel(
    logging.ERROR
)

# Load Gateway Config

with open(
    '../gateway/gateway_config.json',
    'r'
) as f:

    config = json.load(f)

# Gateway Client

client = GatewayClient(
    region_name="us-east-1"
)

# Cognito Token

access_token = (
    client.get_access_token_for_cognito(
        config['cognito_info']['client_info']
    )
)

# MCP Transport

transport = streamablehttp_client(

    config['gateway_url'],

    headers={
        "Authorization":
            f"Bearer {access_token}"
    }
)

# MCP Client

mcp_client = MCPClient(
    lambda: transport
)

mcp_client.__enter__()

# Load MCP Tools

tools = mcp_client.list_tools_sync()

print("\nLoaded MCP Tools:\n")

pdf_tool = None

for tool in tools:

    if "PDFTools" in tool.tool_name:
        pdf_tool = tool

# Bedrock Model

model = BedrockModel(

    model_id=
        "openai.gpt-oss-safeguard-120b",

    temperature=0.3,

    streaming=False,

    region_name="us-east-1"
)

# Supervisor Agent

supervisor_agent = Agent(

    model=model,

    tools=[

        flight_agent,
        weather_agent,
        accommodation_agent,

        pdf_tool
    ],

    system_prompt="""
You are an AI travel supervisor assistant.

Responsibilities:
- Understand user travel requests
- Decide which MCP tools to use
- Use flight tools for flight searches
- Use weather tools for forecasts
- Use accommodation tools for hotels
- Generate clean travel summaries

Rules:
- Never mention tool names
- Never expose internal reasoning
- Never print planning steps
- Do not include markdown tables
- Do not include markdown links
- Do not include raw URLs
- Return clean readable text only
"""
)

print("\n✅ AI Travel Supervisor Ready")
print("Type 'exit' or 'quit' to stop")

while True:

    query = input("\nYou: ")

    if query.lower() in [
        "exit",
        "quit"
    ]:
        break

    try:

        # Supervisor Response

        response = supervisor_agent(
            query
        )

        final_response = str(
            response
        ).strip()

        # Remove URLs

        final_response = re.sub(
            r'http\S+',
            '',
            final_response
        )

        # Remove Markdown Links

        final_response = re.sub(
            r'\[.*?\]\(.*?\)',
            '',
            final_response
        )

        print(
            "\n================ RESPONSE ================\n"
        )

        print(final_response)

        # Generate PDF

        if "pdf" in query.lower():

            print(
                "\n📄 Generating PDF...\n"
            )

            pdf_result = (
                mcp_client.call_tool_sync(

                    "generate-pdf",

                    "PDFTools___generate_travel_pdf",

                    {
                        "report_content":
                            final_response
                    }
                )
            )

            response_text = (
                pdf_result["content"][0]["text"]
            )

            response_json = json.loads(
                response_text
            )

            body_json = json.loads(
                response_json["body"]
            )

            pdf_url = body_json[
                "pdf_url"
            ]

            print(
                "\n✅ PDF URL:\n"
            )

            print(pdf_url)

    except Exception as e:

        print(
            f"\n❌ Error: {e}"
        )