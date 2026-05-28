from dotenv import load_dotenv
from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient

import logging
import json
import os
import ssl
import urllib3

os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['AWS_CA_BUNDLE'] = ''

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


load_dotenv()

client = GatewayClient(
    region_name=os.getenv("AWS_DEFAULT_REGION")
)

try:
    client._session.verify = False
except Exception:
    pass

client.logger.setLevel(logging.DEBUG)

print("Creating Cognito OAuth...")

cognito_response = client.create_oauth_authorizer_with_cognito(
    "FlightAuthorizer"
)

print("Creating Gateway...")

gateway = client.create_mcp_gateway(
    name="Gateway-Travel-Agent-1",
    authorizer_config=cognito_response["authorizer_config"],
    enable_semantic_search=True
)

flight_lambda_arn = os.getenv("FLIGHT_LAMBDA_ARN")
weather_lambda_arn = os.getenv("WEATHER_LAMBDA_ARN")
accommodation_lambda_arn = os.getenv("ACCOMMODATION_LAMBDA_ARN")
pdf_lambda_arn = os.getenv("PDF_LAMBDA_ARN")


flight_tool_schema = [
    {
        "name": "search_flights",
        "description": "Search round trip flights",
        "inputSchema": {
            "type": "object",
            "properties": {
                "departure": {
                    "type": "string",
                    "description": "Departure airport code"
                },
                "arrival": {
                    "type": "string",
                    "description": "Arrival airport code"
                },
                "departure_date": {
                    "type": "string",
                    "description": "Departure date YYYY-MM-DD"
                },
                "return_date": {
                    "type": "string",
                    "description": "Return date YYYY-MM-DD"
                }
            },
            "required": [
                "departure",
                "arrival",
                "departure_date",
                "return_date"
            ]
        }
    }
]

weather_tool_schema = [
    {
        "name": "get_weather_forecast",
        "description": "Get weather forecast for city and date range",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                },
                "start_date": {
                    "type": "string",
                    "description": "Start date YYYY-MM-DD"
                },
                "end_date": {
                    "type": "string",
                    "description": "End date YYYY-MM-DD"
                }
            },
            "required": [
                "city",
                "start_date",
                "end_date"
            ]
        }
    }
]
pdf_tool_schema = [
    {
        "name": "generate_travel_pdf",

        "description":
            "Generate PDF from final travel report",

        "inputSchema": {

            "type": "object",

            "properties": {

                "report_content": {
                    "type": "string",
                    "description":
                        "Final AI generated travel report"
                }
            },

            "required": [
                "report_content"
            ]
        }
    }
]

accommodation_tool_schema = [
    {
        "name": "get_accommodation",
        "description": "Get hotel options for a city",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name"
                },
                "max_price": {
                    "type": "number",
                    "description": "Maximum budget per night"
                }
            },
            "required": [
                "city"
            ]
        }
    }
]

flight_target = client.create_mcp_gateway_target(
    gateway=gateway,
    name="FlightTools",
    target_type="lambda",
    target_payload={
        "lambdaArn": flight_lambda_arn,
        "toolSchema": {
            "inlinePayload": flight_tool_schema
        }
    }
)

print("Flight MCP Tool Added")

weather_target = client.create_mcp_gateway_target(
    gateway=gateway,
    name="WeatherTools",
    target_type="lambda",
    target_payload={
        "lambdaArn": weather_lambda_arn,
        "toolSchema": {
            "inlinePayload": weather_tool_schema
        }
    }
)

print("Weather MCP Tool Added")

accommodation_target = client.create_mcp_gateway_target(
    gateway=gateway,
    name="AccommodationTools",
    target_type="lambda",
    target_payload={
        "lambdaArn": accommodation_lambda_arn,
        "toolSchema": {
            "inlinePayload": accommodation_tool_schema
        }
    }
)
 
print("Accommodation MCP Tool Added")

pdf_target = client.create_mcp_gateway_target(

    gateway=gateway,

    name="PDFTools",

    target_type="lambda",

    target_payload={

        "lambdaArn": pdf_lambda_arn,

        "toolSchema": {
            "inlinePayload": pdf_tool_schema
        }
    }
)

print("PDF MCP Tool Added")

config = {
    "gateway_url": gateway['gatewayUrl'],
    "gateway_id": gateway['gatewayId'],
    "cognito_info": cognito_response,
    "flight_target_id": flight_target['targetId'],
    "weather_target_id": weather_target['targetId'],
    "accommodation_target_id": accommodation_target['targetId'],
    "pdf_target_id": pdf_target['targetId']
}

with open('gateway_config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\nGateway Created Successfully")

print("\nGateway URL:")
print(gateway['gatewayUrl'])

print("\nAvailable MCP Tools:")
print("1. FlightTools___search_flights")
print("2. WeatherTools___get_weather_forecast")
print("3. AccommodationTools___get_accommodation")
print("4. generate_pdf_Tool")
