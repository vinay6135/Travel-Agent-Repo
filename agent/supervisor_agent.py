from strands import Agent
from strands.models import BedrockModel

from flight_agent import run_flight_agent
from weather_agent import run_weather_agent

# =====================================
# Create Supervisor Model
# =====================================

model = BedrockModel(
    model_id="amazon.nova-lite-v1:0",
    temperature=0.3,
    streaming=True
)

# =====================================
# Create Supervisor Agent
# =====================================

supervisor_agent = Agent(

    model=model,

    system_prompt="""
You are a supervisor travel assistant.

Responsibilities:
- Understand user travel requests.
- Decide whether flight agent or weather agent is needed.
- Coordinate specialized agents.
- Combine final responses clearly.
"""
)

print("\n===================================")
print("🧠 Supervisor Agent Ready")
print("Type 'exit' or 'quit' to stop")
print("===================================")

# =====================================
# Chat Loop
# =====================================

while True:

    query = input("\nYou: ")

    if query.lower() in ["exit", "quit"]:
        break

    try:

        flight_response = ""
        weather_response = ""

        # =====================================
        # Flight Intent
        # =====================================

        if any(word in query.lower() for word in [
            "flight",
            "ticket",
            "fly",
            "travel"
        ]):

            print("\n✈️ Flight Agent Working...\n")


        flight_query = f"""
        Find round trip flights mentioned in this request.

        User Request:
        {query}
        """

        flight_response = run_flight_agent(
        flight_query
)

    

        # =====================================
        # Weather Intent
        # =====================================

        if any(word in query.lower() for word in [
            "weather",
            "forecast",
            "temperature",
            "rain"
        ]):

            print("\n🌦️ Weather Agent Working...\n")

            weather_query = f"""
            Provide only weather forecast information from this request.

            User Request:
            {query}
            """

            weather_response = run_weather_agent(
    weather_query
)

        # =====================================
        # Final Combined Output
        # =====================================

        if flight_response:
            print("\n========== Flights ==========\n")
            print(flight_response)

        if weather_response:
            print("\n========== Weather ==========\n")
            print(weather_response)

        # =====================================
        # General Questions
        # =====================================

        if not flight_response and not weather_response:

            print("\n🧠 Supervisor Response:\n")

            response = supervisor_agent(query)

            print(response)

    except Exception as e:

        print(f"\nError: {e}")