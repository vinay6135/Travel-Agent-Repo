import os
import ssl
import urllib3
import logging

from strands import Agent
from strands.models import BedrockModel

from flight_agent import run_flight_agent
from weather_agent import run_weather_agent

# Disable SSL (Hackathon mode)
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['AWS_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ✅ Reduce noisy logs
logging.getLogger().setLevel(logging.ERROR)

# Create Bedrock model
model = BedrockModel(
    model_id="openai.gpt-oss-safeguard-120b",
    temperature=0.3,
    streaming=False,
    region_name="us-east-1"
)

# Create supervisor agent
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
flight_keywords = ["flight", "ticket", "book", "travel", "fly"]
weather_keywords = ["weather", "forecast", "temperature", "rain"]

while True:

    query = input("\nYou: ")

    if query.lower() in ["exit", "quit"]:
        break

    try:
        flight_response = ""
        weather_response = ""

        is_flight = any(word in query.lower() for word in flight_keywords)
        is_weather = any(word in query.lower() for word in weather_keywords)

        # ✅ Flight Agent
        if is_flight:
            print("\n✈️ Flight Agent Working...\n")

            flight_query = f"""
Extract flight details and return only flight results.

User request:
{query}
"""
            flight_response = run_flight_agent(flight_query)

        # ✅ Weather Agent
        if is_weather:
            print("\n🌦️ Weather Agent Working...\n")

            weather_query = f"""
Extract weather request and return forecast.

User request:
{query}
"""
            weather_response = run_weather_agent(weather_query)

        # ✅ ✅ SINGLE CLEAN PRINT (NO DUPLICATION)
        if flight_response or weather_response:

            print("\n================ FINAL RESPONSE ================\n")

            if flight_response:
                print("✈️ Flights:\n")
                print(flight_response.strip())

            if weather_response:
                print("\n🌦️ Weather:\n")
                print(weather_response.strip())

        # ✅ Supervisor handles general queries
        else:
            print("\n🧠 Supervisor Response:\n")

            response = supervisor_agent(query)
            print(str(response).strip())

    except Exception as e:
        print(f"\n❌ Error: {e}")