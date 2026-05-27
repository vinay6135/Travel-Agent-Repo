import json
import requests
import urllib3
import os

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Flight API Key
API_KEY = os.environ["FLIGHT_API_KEY"]

# Fare Class Mapping
fare_class_map = {
    "R": "Economy",
    "Y": "Economy",
    "M": "Economy",
    "K": "Economy",
    "J": "Business",
    "F": "First Class"
}


def lambda_handler(event, context):

    try:

        # Query Parameters
        departure = event.get("departure")
        arrival = event.get("arrival")
        departure_date = event.get("departure_date")
        return_date = event.get("return_date")

        # Validation
        if not departure or not arrival or not departure_date or not return_date:

            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "message": "Please provide departure, arrival, departure_date and return_date"
                })
            }

        # Flight API URL
        url = f"https://api.flightapi.io/roundtrip/{API_KEY}/{departure}/{arrival}/{departure_date}/{return_date}/1/0/0/Economy/USD"

        # API Request
        response = requests.get(url, verify=False)

        print("API URL:", url)
        print("STATUS CODE:", response.status_code)

        # API Error Handling
        if response.status_code != 200:

            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "error",
                    "message": "Failed to fetch flight data",
                    "api_response": response.text
                })
            }

        # JSON Response
        data = response.json()

        itineraries = data.get("itineraries", [])
        legs = data.get("legs", [])
        segments = data.get("segments", [])
        carriers = data.get("carriers", [])
        agents = data.get("agents", [])
        places = data.get("places", [])

        # Carrier Lookup
        carrier_map = {}

        for carrier in carriers:
            carrier_map[carrier["id"]] = carrier["name"]

        # Agent Lookup
        agent_map = {}

        for agent in agents:
            agent_map[agent["id"]] = agent["name"]

        # Place Lookup
        place_map = {}

        for place in places:

            place_map[place["id"]] = {

                "airport": place.get("name"),

                "city": place.get("city_name"),

                "iata": place.get("display_code")
            }

        # Leg Lookup
        leg_map = {}

        for leg in legs:
            leg_map[leg["id"]] = leg

        # Segment Lookup
        segment_map = {}

        for segment in segments:
            segment_map[segment["id"]] = segment

        results = []

        # Deduplication Set
        seen_flights = set()

        # Process Itineraries
        for itinerary in itineraries:

            cheapest_price = itinerary.get(
                "cheapest_price", {}
            ).get("amount")

            leg_ids = itinerary.get("leg_ids", [])

            pricing_options = itinerary.get(
                "pricing_options", []
            )

            if not pricing_options:
                continue

            first_option = pricing_options[0]

            items = first_option.get("items", [])

            if not items:
                continue

            item = items[0]

            # Airlines
            carrier_ids = item.get(
                "marketing_carrier_ids", []
            )

            airline_names = []

            for cid in carrier_ids:

                if cid in carrier_map:
                    airline_names.append(
                        carrier_map[cid]
                    )

            # Booking Agent
            agent_id = item.get("agent_id")

            booking_agent = agent_map.get(
                agent_id,
                "Unknown"
            )

            # Fare Details
            fares = item.get("fares", [])

            booking_code = None
            cabin_class = "Economy"

            if fares:

                booking_code = fares[0].get(
                    "booking_code"
                )

                cabin_class = fare_class_map.get(
                    booking_code,
                    "Economy"
                )

            # Flight Number
            flight_number = None

            segment_ids = item.get("segment_ids", [])

            if segment_ids:

                first_segment = segment_map.get(
                    segment_ids[0]
                )

                if first_segment:

                    flight_number = first_segment.get(
                        "marketing_flight_number"
                    )

            # OUTBOUND

            outbound = {}

            if len(leg_ids) > 0:

                outbound_leg = leg_map.get(
                    leg_ids[0]
                )

                if outbound_leg:

                    origin_place_id = outbound_leg.get(
                        "origin_place_id"
                    )

                    destination_place_id = outbound_leg.get(
                        "destination_place_id"
                    )

                    origin_place = place_map.get(
                        origin_place_id,
                        {}
                    )

                    destination_place = place_map.get(
                        destination_place_id,
                        {}
                    )

                    outbound = {

                        "departure_airport":
                            origin_place.get("airport"),

                        "departure_city":
                            origin_place.get("city")
                            or origin_place.get("airport"),

                        "departure_iata":
                            origin_place.get("iata"),

                        "arrival_airport":
                            destination_place.get("airport"),

                        "arrival_city":
                            destination_place.get("city")
                            or destination_place.get("airport"),

                        "arrival_iata":
                            destination_place.get("iata"),

                        "departure_time":
                            outbound_leg.get("departure"),

                        "arrival_time":
                            outbound_leg.get("arrival"),

                        "duration_minutes":
                            outbound_leg.get("duration"),

                        "stops":
                            outbound_leg.get("stop_count")
                    }

            # RETURN

            inbound = {}

            if len(leg_ids) > 1:

                return_leg = leg_map.get(
                    leg_ids[1]
                )

                if return_leg:

                    origin_place_id = return_leg.get(
                        "origin_place_id"
                    )

                    destination_place_id = return_leg.get(
                        "destination_place_id"
                    )

                    origin_place = place_map.get(
                        origin_place_id,
                        {}
                    )

                    destination_place = place_map.get(
                        destination_place_id,
                        {}
                    )

                    inbound = {

                        "departure_airport":
                            origin_place.get("airport"),

                        "departure_city":
                            origin_place.get("city")
                            or origin_place.get("airport"),

                        "departure_iata":
                            origin_place.get("iata"),

                        "arrival_airport":
                            destination_place.get("airport"),

                        "arrival_city":
                            destination_place.get("city")
                            or destination_place.get("airport"),

                        "arrival_iata":
                            destination_place.get("iata"),

                        "departure_time":
                            return_leg.get("departure"),

                        "arrival_time":
                            return_leg.get("arrival"),

                        "duration_minutes":
                            return_leg.get("duration"),

                        "stops":
                            return_leg.get("stop_count")
                    }

            unique_key = (

                str(airline_names)
                + str(flight_number)
                + str(outbound.get("departure_time"))
                + str(outbound.get("arrival_time"))

            )

            if unique_key in seen_flights:
                continue

            seen_flights.add(unique_key)

            results.append({

                "airlines": airline_names,

                "booking_agent": booking_agent,

                "cabin_class": cabin_class,

                "flight_number": flight_number,

                "price_usd": cheapest_price,

                "outbound": outbound,

                "return": inbound
            })

        results = sorted(
            results,
            key=lambda x: x["price_usd"]
            if x["price_usd"] else 999999
        )

        return {

            "statusCode": 200,

            "body": json.dumps({

                "status": "success",

                "total_flights": len(results),

                "data": results
            })
        }

    except Exception as e:

        return {

            "statusCode": 500,

            "body": json.dumps({
                "status": "error",
                "message": str(e)
            })
        }