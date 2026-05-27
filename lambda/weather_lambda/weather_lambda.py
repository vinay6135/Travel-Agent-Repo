import json
import requests
import os
from datetime import datetime

API_KEY = os.environ["OPENWEATHER_API_KEY"]


def lambda_handler(event, context):

    try:

        tool_name = "unknown"

        if context.client_context is not None and hasattr(
            context.client_context,
            'custom'
        ):

            full_tool_name = context.client_context.custom.get(
                'bedrockAgentCoreToolName',
                'unknown'
            )

            if '___' in full_tool_name:
                tool_name = full_tool_name.split('___')[1]
            else:
                tool_name = full_tool_name

        if tool_name != "get_weather_forecast":

            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"Unknown tool: {tool_name}"
                })
            }

        city = event.get("city")
        start_date = event.get("start_date")
        end_date = event.get("end_date")

        geo_response = requests.get(

            "http://api.openweathermap.org/geo/1.0/direct",

            params={
                "q": city,
                "limit": 1,
                "appid": API_KEY
            }
        )

        geo_data = geo_response.json()

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        weather_response = requests.get(

            "https://api.openweathermap.org/data/2.5/forecast",

            params={
                "lat": lat,
                "lon": lon,
                "appid": API_KEY,
                "units": "metric"
            }
        )

        weather_data = weather_response.json()

        forecasts = weather_data.get(
            "list",
            []
        )

        results = []

        start_obj = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        )

        end_obj = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        )

        for item in forecasts:

            forecast_time = datetime.strptime(
                item["dt_txt"],
                "%Y-%m-%d %H:%M:%S"
            )

            if start_obj.date() <= forecast_time.date() <= end_obj.date():

                results.append({

                    "datetime":
                        item["dt_txt"],

                    "temperature":
                        item["main"]["temp"],

                    "weather":
                        item["weather"][0]["description"],

                    "humidity":
                        item["main"]["humidity"]
                })

        return {

            "statusCode": 200,

            "body": json.dumps({

                "city": city,

                "forecast": results[:15]
            })
        }

    except Exception as e:

        return {

            "statusCode": 500,

            "body": json.dumps({
                "error": str(e)
            })
        }