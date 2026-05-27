from bedrock_agentcore_starter_toolkit.operations.gateway.client import GatewayClient
import logging
import json

client = GatewayClient(region_name="us-east-1")

client.logger.setLevel(logging.DEBUG)

print("Creating Cognito OAuth...")

cognito_response = client.create_oauth_authorizer_with_cognito(
    "FlightAuthorizer"
)

print("Creating Gateway...")

gateway = client.create_mcp_gateway(

    name="FlightGateway-MCP-1",

    authorizer_config=
        cognito_response["authorizer_config"],

    enable_semantic_search=True
)

# =====================================
# Lambda ARNs
# =====================================

flight_lambda_arn = (
    "arn:aws:lambda:us-east-1:271376211872:function:Searchroundtripflight"
)

weather_lambda_arn = (
    "arn:aws:lambda:us-east-1:271376211872:function:weather_lambda_1"
)

# =====================================
# Flight Tool Schema
# =====================================

flight_tool_schema = [
    {
        "name": "search_flights",

        "description":
            "Search round trip flights",

        "inputSchema": {

            "type": "object",

            "properties": {

                "departure": {
                    "type": "string",
                    "description":
                        "Departure airport code"
                },

                "arrival": {
                    "type": "string",
                    "description":
                        "Arrival airport code"
                },

                "departure_date": {
                    "type": "string",
                    "description":
                        "Departure date YYYY-MM-DD"
                },

                "return_date": {
                    "type": "string",
                    "description":
                        "Return date YYYY-MM-DD"
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

# =====================================
# Weather Tool Schema
# =====================================

weather_tool_schema = [
    {
        "name": "get_weather_forecast",

        "description":
            "Get weather forecast for city and date range",

        "inputSchema": {

            "type": "object",

            "properties": {

                "city": {
                    "type": "string",
                    "description":
                        "City name"
                },

                "start_date": {
                    "type": "string",
                    "description":
                        "Start date YYYY-MM-DD"
                },

                "end_date": {
                    "type": "string",
                    "description":
                        "End date YYYY-MM-DD"
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

# =====================================
# Create Flight MCP Target
# =====================================

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

# =====================================
# Create Weather MCP Target
# =====================================

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

# =====================================
# Save Config
# =====================================

config = {

    "gateway_url":
        gateway['gatewayUrl'],

    "gateway_id":
        gateway['gatewayId'],

    "cognito_info":
        cognito_response,

    "flight_target_id":
        flight_target['targetId'],

    "weather_target_id":
        weather_target['targetId']
}

with open(
    'gateway_config.json',
    'w'
) as f:

    json.dump(config, f, indent=2)

# =====================================
# Success Output
# =====================================

print("\nGateway Created Successfully")

print("\nGateway URL:")
print(gateway['gatewayUrl'])

print("\nAvailable MCP Tools:")
print("1. FlightTools___search_flights")
print("2. WeatherTools___get_weather_forecast")