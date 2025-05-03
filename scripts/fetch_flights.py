import os
import json
import requests
import csv
from datetime import datetime, date
from time import sleep
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('API_KEY')
CREATE_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create"
POLL_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/poll"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# File paths
FILTERED_JSON = "data/ranked_cities_top100.json"
OUTPUT_JSON = "data/enriched_routes.json"
AIRPORTS_CSV = "data/iata_airports_and_locations_with_vibes.csv"
USER_INFO_JSON = "i_json/user_info.json"

# Load airport data from CSV
def load_airport_data(file_path: str) -> Dict[str, Dict]:
    airports = {}
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse vibes from string to dictionary if not null
                vibes = {}
                if row.get('vibes') and row['vibes'] != 'null':
                    try:
                        vibes = json.loads(row['vibes'].replace('""', '"'))
                    except json.JSONDecodeError:
                        pass
                
                airports[row['en-GB']] = {
                    'iata': row['IATA'],
                    'latitude': float(row['latitude']) if row['latitude'] else None,
                    'longitude': float(row['longitude']) if row['longitude'] else None,
                    'vibes': vibes
                }
    except Exception as e:
        print(f"Error loading airport data: {str(e)}")
        return {}
    return airports

# Load user information
def load_user_info(file_path: str) -> Dict:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading user info: {str(e)}")
        return {}

# Read filtered routes
def load_filtered_routes(file_path: str) -> List[Dict]:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading filtered routes: {str(e)}")
        return []

# Create session
def create_session(origin: str, destination: str, departure_date: date, return_date: Optional[date] = None):
    query = {
        "market": "ES",  # Could be dynamically determined based on user location
        "locale": "en-GB",
        "currency": "EUR",
        "queryLegs": [
            {
                "originPlace": {"iata": origin},
                "destinationPlace": {"iata": destination},
                "date": {
                    "year": departure_date.year,
                    "month": departure_date.month,
                    "day": departure_date.day
                }
            }
        ],
        "cabinClass": "CABIN_CLASS_ECONOMY",
        "adults": 1  # Could be based on number of travelers
    }
    
    # Add return leg if return date is provided
    if return_date:
        query["queryLegs"].append({
            "originPlace": {"iata": destination},
            "destinationPlace": {"iata": origin},
            "date": {
                "year": return_date.year,
                "month": return_date.month,
                "day": return_date.day
            }
        })
    
    payload = {"query": query}
    
    try:
        res = requests.post(CREATE_URL, headers=HEADERS, json=payload)
        res.raise_for_status()
        return res.json()["sessionToken"]
    except Exception as e:
        print(f"Error creating session for {destination}: {str(e)}")
        return None

# Poll session
def poll_results(token: str) -> Dict:
    url = f"{POLL_URL}/{token}"
    for _ in range(10):  # Try up to 10 times
        try:
            res = requests.post(url, headers=HEADERS)
            res.raise_for_status()
            data = res.json()
            if data.get("status") == "UpdatesComplete":
                return data
            sleep(1)
        except Exception as e:
            print(f"Error polling results: {str(e)}")
            sleep(1)
    raise Exception("Polling timed out")

# Extract flight data
def extract_flight_data(poll_data: Dict) -> List[Dict]:
    if not poll_data or "content" not in poll_data:
        return []
    
    content = poll_data.get("content", {})
    results = content.get("results", {})
    itineraries = results.get("itineraries", {})
    
    flights = []
    for key, itinerary in itineraries.items():
        # Get pricing information
        pricing_options = itinerary.get("pricingOptions", [])
        if not pricing_options:
            continue
            
        pricing = pricing_options[0].get("price", {}).get("amount")
        
        # Get leg information
        leg_ids = itinerary.get("legIds", [])
        if not leg_ids:
            continue
            
        leg_id = leg_ids[0]
        leg = results.get("legs", {}).get(leg_id, {})
        
        # Get carrier information
        carriers = leg.get("carriers", [])
        if carriers:
            carrier_id = carriers[0]
            carrier_name = results.get("carriers", {}).get(carrier_id, {}).get("name", "Unknown Airline")
        else:
            carrier_name = "Unknown Airline"
        
        # Create flight record
        flight = {
            "price_eur": pricing,
            "airline": carrier_name,
            "departure_time": leg.get("departureDateTime"),
            "arrival_time": leg.get("arrivalDateTime"),
            "duration_minutes": leg.get("durationInMinutes")
        }
        flights.append(flight)
    
    # Sort by price (cheapest first)
    return sorted(flights, key=lambda x: x.get("price_eur", float("inf")))

# Add grading based on user preferences
def compute_grade(flight: Dict, traveler: Dict, city_vibes: Dict) -> float:
    score = 0
    
    # Price score - higher score for prices within budget range
    if flight["price_eur"] is not None:
        min_budget = float(traveler.get("budgetRange", {}).get("min", 0))
        max_budget = float(traveler.get("budgetRange", {}).get("max", 2000))
        
        # If price is under max budget, give points
        if flight["price_eur"] <= max_budget:
            # Best score if price is right in the middle of the budget range
            ideal_price = (min_budget + max_budget) / 2
            price_score = 1 - abs(flight["price_eur"] - ideal_price) / max_budget
            score += price_score * 5  # Weight price heavily
    
    # Duration score - shorter is better
    if flight.get("duration_minutes"):
        # Give full points for flights under 120 minutes, decreasing to 0 for flights over 720 minutes
        max_duration = 720  # 12 hours
        duration_score = max(0, (max_duration - flight["duration_minutes"]) / max_duration)
        score += duration_score * 3
    
    # Vibe score - match with traveler preferences
    preferred_vibes = traveler.get("preferredVibes", [])
    if preferred_vibes and city_vibes:
        matches = 0
        for vibe in preferred_vibes:
            if city_vibes.get(vibe) == "1":
                matches += 1
        
        vibe_score = matches / len(preferred_vibes) if preferred_vibes else 0
        score += vibe_score * 4
    
    return round(score, 2)

# Main function
def main():
    # Load all necessary data
    airports = load_airport_data(AIRPORTS_CSV)
    user_info = load_user_info(USER_INFO_JSON)
    destinations = load_filtered_routes(FILTERED_JSON)
    
    # Get dates and travelers from user info
    date_range = user_info.get("dateRange", {})
    departure_date = datetime.fromisoformat(date_range.get("startDate")).date() if date_range.get("startDate") else date.today()
    return_date = datetime.fromisoformat(date_range.get("endDate")).date() if date_range.get("endDate") else None
    
    travelers = user_info.get("travelers", [])
    if not travelers:
        print("No traveler information found!")
        return
    
    # Use the first traveler's starting point as default
    origin_city = travelers[0].get("startingPoint", "Madrid")
    origin_iata = None
    
    # Find IATA code for origin city
    for city, data in airports.items():
        if city.lower() == origin_city.lower():
            origin_iata = data['iata']
            break
    
    if not origin_iata:
        print(f"Could not find IATA code for {origin_city}, using 'MAD' as default")
        origin_iata = "MAD"
    
    enriched_destinations = []
    
    # Process each destination
    for dest in destinations:
        city_name = dest["city"]
        print(f"Processing {city_name}...")
        
        # Find the IATA code for this city
        destination_iata = None
        city_vibes = {}
        for airport_city, data in airports.items():
            if city_name.lower() in airport_city.lower() or airport_city.lower() in city_name.lower():
                destination_iata = data['iata']
                city_vibes = data.get('vibes', {})
                break
        
        if not destination_iata:
            print(f"Could not find IATA code for {city_name}, skipping")
            dest["flight_score"] = 0
            dest["note"] = "No IATA code found"
            enriched_destinations.append(dest)
            continue
        
        # Add IATA code to destination info
        dest["iata"] = destination_iata
        
        # Search for flights
        try:
            token = create_session(origin_iata, destination_iata, departure_date, return_date)
            if not token:
                raise Exception("Failed to create session")
                
            poll_data = poll_results(token)
            flights = extract_flight_data(poll_data)
            
            # If flights found, add the best one to destination info
            if flights:
                best_flight = flights[0]
                dest.update(best_flight)
                
                # Calculate scores for each traveler
                traveler_scores = []
                for traveler in travelers:
                    score = compute_grade(best_flight, traveler, city_vibes)
                    traveler_scores.append({
                        "travelerNumber": traveler.get("travelerNumber"),
                        "score": score
                    })
                
                # Average score across all travelers
                dest["flight_score"] = round(sum(ts["score"] for ts in traveler_scores) / len(traveler_scores), 2)
                dest["traveler_scores"] = traveler_scores
            else:
                dest["flight_score"] = 0
                dest["note"] = "No flights found"
        except Exception as e:
            dest["flight_score"] = 0
            dest["note"] = f"Error: {str(e)}"
        
        enriched_destinations.append(dest)
    
    # Sort destinations by flight score (highest first)
    enriched_destinations.sort(key=lambda x: x.get("flight_score", 0), reverse=True)
    
    # Update ranks
    for i, dest in enumerate(enriched_destinations, 1):
        dest["rank"] = i
    
    # Save enriched results
    with open(OUTPUT_JSON, "w") as f:
        json.dump(enriched_destinations, f, indent=2)
    
    print(f"Done. Results saved to {OUTPUT_JSON}")
    
    # Print top destinations for quick review
    print("\nTop 5 destinations:")
    for dest in enriched_destinations[:5]:
        price = f"€{dest.get('price_eur', 'N/A')}" if dest.get('price_eur') is not None else "N/A"
        print(f"{dest['rank']}. {dest['city']} - Score: {dest.get('flight_score', 0)}, Price: {price}")

if __name__ == "__main__":
    main()