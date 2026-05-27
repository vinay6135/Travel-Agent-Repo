import json
import requests
import urllib3
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_KEY = os.environ["FLIGHT_API_KEY"]

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

        departure = event.get("departure")
        arrival = event.get("arrival")
        departure_date = event.get("departure_date")
        return_date = event.get("return_date")

        if not departure or not arrival or not departure_date or not return_date:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "status": "error",
                    "message": "Please provide all inputs"
                })
            }

        url = f"https://api.flightapi.io/roundtrip/{API_KEY}/{departure}/{arrival}/{departure_date}/{return_date}/1/0/0/Economy/USD"

        response = requests.get(url, verify=False)

        if response.status_code != 200:
            return {
                "statusCode": 500,
                "body": json.dumps({
                    "status": "error",
                    "message": "API failed",
                    "api_response": response.text
                })
            }

        data = response.json()

        itineraries = data.get("itineraries", [])
        legs = data.get("legs", [])
        segments = data.get("segments", [])
        carriers = data.get("carriers", [])
        agents = data.get("agents", [])
        places = data.get("places", [])

        carrier_map = {c["id"]: c["name"] for c in carriers}
        agent_map = {a["id"]: a["name"] for a in agents}

        place_map = {
            p["id"]: {
                "airport": p.get("name"),
                "city": p.get("city_name"),
                "iata": p.get("display_code")
            }
            for p in places
        }

        leg_map = {l["id"]: l for l in legs}
        segment_map = {s["id"]: s for s in segments}

        results = []
        seen_flights = set()

        for itinerary in itineraries:

            cheapest_price = itinerary.get("cheapest_price", {}).get("amount")
            leg_ids = itinerary.get("leg_ids", [])

            pricing_options = itinerary.get("pricing_options", [])
            if not pricing_options:
                continue

            item = pricing_options[0].get("items", [])[0]

            # Airlines
            airline_names = [
                carrier_map[cid] for cid in item.get("marketing_carrier_ids", [])
                if cid in carrier_map
            ]

            # Flight number
            flight_number = None
            segment_ids = item.get("segment_ids", [])

            if segment_ids:
                first_segment = segment_map.get(segment_ids[0])
                if first_segment:
                    flight_number = first_segment.get("marketing_flight_number")

            # OUTBOUND
            outbound = {}
            if len(leg_ids) > 0:
                leg = leg_map.get(leg_ids[0])
                if leg:
                    origin = place_map.get(leg.get("origin_place_id"), {})
                    dest = place_map.get(leg.get("destination_place_id"), {})
                    outbound = {
                        "departure_time": leg.get("departure"),
                        "arrival_time": leg.get("arrival"),
                        "duration_minutes": leg.get("duration"),
                        "stops": leg.get("stop_count")
                    }

            # RETURN
            inbound = {}
            if len(leg_ids) > 1:
                leg = leg_map.get(leg_ids[1])
                if leg:
                    inbound = {
                        "departure_time": leg.get("departure"),
                        "arrival_time": leg.get("arrival"),
                        "duration_minutes": leg.get("duration"),
                        "stops": leg.get("stop_count")
                    }

            key = str(airline_names) + str(flight_number) + str(outbound.get("departure_time"))

            if key in seen_flights:
                continue
            seen_flights.add(key)

            results.append({
                "airlines": airline_names,
                "flight_number": flight_number,
                "price_usd": cheapest_price,
                "outbound": outbound,
                "return": inbound
            })

        # ✅ SORT BY PRICE
        results = sorted(
            results,
            key=lambda x: x["price_usd"] if x["price_usd"] else 999999
        )

        # ✅ CHEAPEST PER AIRLINE
        cheapest_per_airline = {}

        for flight in results:
            airlines = flight.get("airlines", [])

            airline_key = ", ".join(airlines) if airlines else "Unknown"
            price = flight.get("price_usd", 999999)

            if airline_key not in cheapest_per_airline:
                cheapest_per_airline[airline_key] = flight
            else:
                existing_price = cheapest_per_airline[airline_key]["price_usd"]
                if price < existing_price:
                    cheapest_per_airline[airline_key] = flight

        # ✅ FINAL FILTER
        filtered_results = list(cheapest_per_airline.values())

        filtered_results = sorted(
            filtered_results,
            key=lambda x: x["price_usd"] if x["price_usd"] else 999999
        )

        results = filtered_results[:4]

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