import os
import json
import requests
import csv
from datetime import datetime, date
from time import sleep
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
API_KEY = os.getenv('API_KEY')
print(f"API Key Loaded: {'Yes' if API_KEY else 'No'}") # Verify API key is loaded
if not API_KEY:
    print("CRITICAL: Skyscanner API Key not found in environment variables (.env file). Exiting.")
    exit()

CREATE_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create"
POLL_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/poll"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# File paths
# Assuming the input JSON from Prolog now contains 'city' and 'iata'
FILTERED_JSON = "data/ranked_cities_top100.json"
OUTPUT_JSON = "data/enriched_routes.json"
AIRPORTS_CSV = "data/iata_airports_and_locations_with_vibes.csv"
USER_INFO_JSON = "i_json/user_info.json"

# --- Data Loading Functions ---

def load_airport_data_by_iata(file_path: str) -> Dict[str, Dict]:
    """Loads airport data from CSV, keyed by IATA code."""
    airports_by_iata = {}
    print(f"Loading airport data (keyed by IATA) from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            count = 0
            missing_iata_count = 0
            for row in reader:
                iata_code = row.get('IATA')
                if not iata_code:
                    missing_iata_count += 1
                    continue # Skip rows without IATA

                # Parse vibes safely
                vibes = {}
                vibes_str = row.get('vibes')
                if vibes_str and vibes_str.lower() != 'null':
                    try:
                        # Basic cleaning attempts for common JSON issues
                        vibes_str = vibes_str.strip()
                        if vibes_str.startswith('"') and vibes_str.endswith('"'):
                             vibes_str = vibes_str[1:-1] # Remove wrapping quotes
                        vibes_str = vibes_str.replace('""', '"') # Handle double quotes
                        vibes = json.loads(vibes_str)
                    except json.JSONDecodeError:
                        try:
                            # Try replacing single quotes if they were used
                            vibes_str_fixed = vibes_str.replace("'", '"')
                            vibes = json.loads(vibes_str_fixed)
                        except json.JSONDecodeError as json_err:
                            # Only print warning if parsing fails after attempts
                            # print(f"Warning: Could not parse vibes JSON for IATA {iata_code}: {row['vibes']} - Error: {json_err}")
                            pass # Keep vibes as empty dict

                airports_by_iata[iata_code] = {
                    'name': row.get('en-GB', 'Unknown Name'), # Store name for reference
                    'latitude': float(row['latitude']) if row.get('latitude') else None,
                    'longitude': float(row['longitude']) if row.get('longitude') else None,
                    'vibes': vibes
                }
                count += 1

        print(f"Loaded data for {count} airports keyed by IATA.")
        if missing_iata_count > 0:
            print(f"Warning: Skipped {missing_iata_count} rows due to missing IATA codes.")
        return airports_by_iata

    except FileNotFoundError:
        print(f"CRITICAL Error: Airport data file not found at {file_path}. Exiting.")
        exit()
    except Exception as e:
        print(f"CRITICAL Error loading airport data: {str(e)}. Exiting.")
        exit()

def find_iata_for_city(city_name: str, airports_csv_path: str) -> Optional[str]:
    """Finds the most likely IATA for a given city name by searching the airports CSV."""
    print(f"Attempting to find IATA for origin city: '{city_name}'...")
    normalized_origin_city = city_name.lower().strip()
    potential_matches = []

    try:
        with open(airports_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                iata_code = row.get('IATA')
                airport_name = row.get('en-GB')
                if not iata_code or not airport_name:
                    continue

                normalized_airport_name = airport_name.lower().strip()
                quality = 0

                # Assign quality score based on match type
                if normalized_origin_city == normalized_airport_name:
                    quality = 3 # Exact match
                elif normalized_airport_name.startswith(normalized_origin_city + " ") or normalized_airport_name == normalized_origin_city:
                    quality = 2 # Airport name starts with city name
                elif len(normalized_origin_city) > 3 and (f" {normalized_origin_city} " in f" {normalized_airport_name} " or normalized_airport_name.startswith(f"{normalized_origin_city} ")):
                     quality = 1 # Airport name contains city name (common)
                elif len(normalized_airport_name) > 4 and (f" {normalized_airport_name} " in f" {normalized_origin_city} " or normalized_origin_city.endswith(f" {normalized_airport_name}")):
                     quality = 1 # City name contains airport name (less common)

                if quality > 0:
                    potential_matches.append({'iata': iata_code, 'name': airport_name, 'quality': quality})

        if not potential_matches:
            print(f"Warning: No potential IATA matches found for origin city '{city_name}'.")
            return None

        # Sort by quality descending
        potential_matches.sort(key=lambda x: x['quality'], reverse=True)
        best_match = potential_matches[0]
        print(f"Found best origin IATA {best_match['iata']} for '{city_name}' via airport entry '{best_match['name']}' (Quality: {best_match['quality']})")
        return best_match['iata']

    except FileNotFoundError:
        print(f"Error: Airport data file not found at {airports_csv_path} while searching for origin IATA.")
        return None
    except Exception as e:
        print(f"Error finding origin IATA for '{city_name}': {str(e)}")
        return None


def load_user_info(file_path: str) -> Dict:
    """Loads user information from JSON file."""
    print(f"Loading user info from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            user_info = json.load(f)
        # Basic validation
        if "travelers" not in user_info or not user_info["travelers"]:
            print("CRITICAL Error: User info file must contain a non-empty 'travelers' list. Exiting.")
            exit()
        if "dateRange" not in user_info:
             print("CRITICAL Error: User info file must contain 'dateRange'. Exiting.")
             exit()
        print("User info loaded successfully.")
        return user_info
    except FileNotFoundError:
        print(f"CRITICAL Error: User info file not found at {file_path}. Exiting.")
        exit()
    except json.JSONDecodeError as e:
        print(f"CRITICAL Error decoding JSON from user info file {file_path}: {str(e)}. Exiting.")
        exit()
    except Exception as e:
        print(f"CRITICAL Error loading user info: {str(e)}. Exiting.")
        exit()

def load_filtered_routes(file_path: str) -> List[Dict]:
    """Loads filtered destinations (expecting 'city' and 'iata') from JSON file."""
    print(f"Loading filtered destinations from {file_path}...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            routes = json.load(f)
        if not isinstance(routes, list):
             print(f"CRITICAL Error: Filtered routes file {file_path} should contain a JSON list. Exiting.")
             exit()
        print(f"Loaded {len(routes)} filtered destinations.")
        return routes
    except FileNotFoundError:
        print(f"CRITICAL Error: Filtered routes file not found at {file_path}. Exiting.")
        exit()
    except json.JSONDecodeError as e:
        print(f"CRITICAL Error decoding JSON from filtered routes file {file_path}: {str(e)}. Exiting.")
        exit()
    except Exception as e:
        print(f"CRITICAL Error loading filtered routes: {str(e)}. Exiting.")
        exit()


# --- Skyscanner API Functions --- (Mostly unchanged, minor logging tweaks)

def create_session(origin: str, destination: str, departure_date: date, return_date: Optional[date] = None) -> Optional[str]:
    """Creates a flight search session with Skyscanner API V3."""
    query = {
        "market": "ES", # Assuming market, adjust if needed
        "locale": "en-GB",
        "currency": "EUR", # Assuming currency
        "queryLegs": [
            {
                "originPlaceId": {"iata": origin},
                "destinationPlaceId": {"iata": destination},
                "date": {
                    "year": departure_date.year,
                    "month": departure_date.month,
                    "day": departure_date.day
                }
            }
        ],
        "cabinClass": "CABIN_CLASS_ECONOMY",
        "adults": 1 # Assuming 1 adult, adjust if needed based on user_info
    }

    if return_date:
        query["queryLegs"].append({
            "originPlaceId": {"iata": destination},
            "destinationPlaceId": {"iata": origin},
            "date": {
                "year": return_date.year,
                "month": return_date.month,
                "day": return_date.day
            }
        })

    payload = {"query": query}
    print(f"Attempting to create session: {origin} -> {destination} on {departure_date}")
    # print(f"Payload: {json.dumps(payload, indent=2)}") # Uncomment for debugging

    try:
        res = requests.post(CREATE_URL, headers=HEADERS, json=payload, timeout=30)
        print(f"Create session response status code for {destination}: {res.status_code}")

        if res.status_code != 200:
            print(f"Error creating session for {destination}: Status Code {res.status_code}")
            error_details = {}
            try:
                error_details = res.json()
                print(f"API Error Response: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"API Error Response (non-JSON): {res.text}")
            # Check for specific invalid IATA error
            if "QueryPlace ID is not valid IATA" in error_details.get("message", "") or "INVALID_PLACE" in str(error_details):
                 print(f"*** API rejected IATA code '{destination}'. Please verify the IATA in the input file '{FILTERED_JSON}'. ***")
            return None

        response_json = res.json()
        session_token = response_json.get("sessionToken")
        if not session_token:
             print(f"Error: Session token not found in successful response for {destination}. Response: {response_json}")
             return None

        print(f"Session created successfully for {destination}.")
        return session_token

    except requests.exceptions.Timeout:
        print(f"Error creating session for {destination}: Request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error creating session for {destination}: Request failed: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during session creation for {destination}: {str(e)}")
        return None

def poll_results(token: str) -> Optional[Dict]:
    """Polls Skyscanner API for flight results using the session token."""
    url = f"{POLL_URL}/{token}"
    print(f"Polling results for token: ...{token[-6:]}")
    initial_wait = 1
    sleep(initial_wait)
    max_attempts = 15
    base_sleep = 2

    for attempt in range(max_attempts):
        print(f"Polling attempt {attempt + 1}/{max_attempts}...")
        try:
            res = requests.post(url, headers=HEADERS, timeout=25)
            # print(f"Poll response status code: {res.status_code}") # Optional debug logging

            if res.status_code != 200:
                 print(f"Error polling results (Status {res.status_code})")
                 try:
                     print(f"Poll Error Response: {res.text}")
                 except Exception: pass
                 # Handle specific errors if needed (400, 410, 429)
                 if res.status_code in [400, 410]: # Bad request or session expired
                     print("Polling failed: Invalid session or expired.")
                     return None
                 elif res.status_code == 429:
                     print("Rate limit hit during polling. Waiting longer...")
                     sleep(10)
                     continue # Retry same attempt count
                 res.raise_for_status() # Raise for other errors

            data = res.json()
            status = data.get("status")
            # print(f"Polling status: {status}") # Optional debug logging

            if status == "RESULT_STATUS_COMPLETE":
                print("Polling complete.")
                return data
            elif status in ["RESULT_STATUS_INCOMPLETE", "RESULT_STATUS_PARTIAL", "RESULT_STATUS_UPDATING"]:
                 current_sleep = base_sleep + attempt
                 # print(f"Results not ready, sleeping for {current_sleep} seconds...") # Optional debug
                 sleep(current_sleep)
            elif status == "RESULT_STATUS_FAILED":
                 print(f"Warning: Polling status indicates failure. Response: {data}")
                 return None # Indicate failure
            else:
                 print(f"Warning: Unexpected polling status '{status}'. Retrying...")
                 sleep(base_sleep)

        except requests.exceptions.Timeout:
            print(f"Polling attempt {attempt + 1} timed out.")
            sleep(base_sleep + attempt)
        except requests.exceptions.RequestException as e:
            print(f"Error polling results (attempt {attempt + 1}): {str(e)}")
            sleep(base_sleep * 2)
        except Exception as e:
            print(f"Unexpected error during polling (attempt {attempt + 1}): {str(e)}")
            sleep(base_sleep)

    print("Error: Polling timed out or failed after multiple attempts.")
    return None # Indicate failure

def extract_flight_data(poll_data: Dict) -> List[Dict]:
    """Extracts and sorts flight details from the poll response."""
    if not poll_data or "content" not in poll_data:
        print("Warning: No 'content' found in poll data for extraction.")
        return []

    content = poll_data.get("content", {})
    results = content.get("results", {})
    itineraries = results.get("itineraries", {})
    legs = results.get("legs", {})
    carriers = results.get("carriers", {})
    places = results.get("places", {})

    if not itineraries:
        # print("No itineraries found in results.") # Common, reduce noise
        return []

    flights = []
    # print(f"Extracting data from {len(itineraries)} itineraries...") # Optional debug
    itinerary_count = 0
    processed_count = 0

    for key, itinerary in itineraries.items():
        itinerary_count += 1
        pricing_options = itinerary.get("pricingOptions", [])
        if not pricing_options:
            continue

        try:
            cheapest_option = min(pricing_options, key=lambda x: float(x.get("price", {}).get("amount", "inf") or "inf"))
            price_str = cheapest_option.get("price", {}).get("amount")
            if price_str is None or price_str == "inf":
                 continue
            # Price is often in thousandths of the currency unit (e.g., milli-euros)
            price = int(price_str) / 1000.0
        except (ValueError, TypeError):
             # print(f"Warning: Could not parse price for itinerary {key}.") # Optional debug
             continue

        leg_ids = itinerary.get("legIds", [])
        if not leg_ids:
            continue

        # --- Process Outbound Leg ---
        outbound_leg_id = leg_ids[0]
        outbound_leg_data = legs.get(outbound_leg_id)
        if not outbound_leg_data:
            continue

        operating_carrier_ids_out = outbound_leg_data.get("operatingCarrierIds", [])
        carrier_name_out = carriers.get(operating_carrier_ids_out[0], {}).get("name", "Unknown Airline") if operating_carrier_ids_out else "Unknown Airline"

        departure_out = outbound_leg_data.get("departureDateTime", {})
        arrival_out = outbound_leg_data.get("arrivalDateTime", {})
        departure_time_str_out = f"{departure_out.get('year')}-{departure_out.get('month'):02d}-{departure_out.get('day'):02d}T{departure_out.get('hour'):02d}:{departure_out.get('minute'):02d}:00" if departure_out.get('year') else None
        arrival_time_str_out = f"{arrival_out.get('year')}-{arrival_out.get('month'):02d}-{arrival_out.get('day'):02d}T{arrival_out.get('hour'):02d}:{arrival_out.get('minute'):02d}:00" if arrival_out.get('year') else None
        duration_out = outbound_leg_data.get("durationInMinutes")
        origin_id_out = outbound_leg_data.get("originPlaceId")
        destination_id_out = outbound_leg_data.get("destinationPlaceId")
        origin_airport_out = places.get(origin_id_out, {}).get("iata")
        destination_airport_out = places.get(destination_id_out, {}).get("iata")

        # --- Process Return Leg (if exists) ---
        return_leg_data = None
        carrier_name_ret, departure_time_str_ret, arrival_time_str_ret, duration_ret, origin_airport_ret, destination_airport_ret = [None] * 6
        if len(leg_ids) > 1:
            return_leg_id = leg_ids[1]
            return_leg_data = legs.get(return_leg_id)
            if return_leg_data:
                 operating_carrier_ids_ret = return_leg_data.get("operatingCarrierIds", [])
                 carrier_name_ret = carriers.get(operating_carrier_ids_ret[0], {}).get("name", "Unknown Airline") if operating_carrier_ids_ret else "Unknown Airline"
                 departure_ret = return_leg_data.get("departureDateTime", {})
                 arrival_ret = return_leg_data.get("arrivalDateTime", {})
                 departure_time_str_ret = f"{departure_ret.get('year')}-{departure_ret.get('month'):02d}-{departure_ret.get('day'):02d}T{departure_ret.get('hour'):02d}:{departure_ret.get('minute'):02d}:00" if departure_ret.get('year') else None
                 arrival_time_str_ret = f"{arrival_ret.get('year')}-{arrival_ret.get('month'):02d}-{arrival_ret.get('day'):02d}T{arrival_ret.get('hour'):02d}:{arrival_ret.get('minute'):02d}:00" if arrival_ret.get('year') else None
                 duration_ret = return_leg_data.get("durationInMinutes")
                 origin_id_ret = return_leg_data.get("originPlaceId")
                 destination_id_ret = return_leg_data.get("destinationPlaceId")
                 origin_airport_ret = places.get(origin_id_ret, {}).get("iata")
                 destination_airport_ret = places.get(destination_id_ret, {}).get("iata")

        # --- Assemble Flight Data ---
        flight = {
            "price_eur": price,
            "outbound_airline": carrier_name_out,
            "outbound_departure_time": departure_time_str_out,
            "outbound_arrival_time": arrival_time_str_out,
            "outbound_duration_minutes": duration_out,
            "outbound_origin_airport": origin_airport_out,
            "outbound_destination_airport": destination_airport_out,
            "return_airline": carrier_name_ret,
            "return_departure_time": departure_time_str_ret,
            "return_arrival_time": arrival_time_str_ret,
            "return_duration_minutes": duration_ret,
            "return_origin_airport": origin_airport_ret,
            "return_destination_airport": destination_airport_ret,
        }
        flights.append(flight)
        processed_count += 1

    # print(f"Extracted data for {processed_count}/{itinerary_count} flights.") # Optional debug
    return sorted(flights, key=lambda x: x.get("price_eur", float("inf")))

# --- Scoring Function --- (Unchanged)
def compute_grade(flight: Dict, traveler: Dict, city_vibes: Dict) -> float:
    """Computes a score for a flight based on traveler preferences and city vibes."""
    score = 0.0
    price_weight = 5.0
    duration_weight = 3.0
    vibe_weight = 4.0

    # Price score
    price = flight.get("price_eur")
    if price is not None:
        # Ensure budget values are floats
        try:
            min_budget = float(traveler.get("budgetRange", {}).get("min", 0))
            max_budget = float(traveler.get("budgetRange", {}).get("max", 5000))
        except (ValueError, TypeError):
             print(f"Warning: Invalid budget format for traveler {traveler.get('travelerNumber')}. Using defaults.")
             min_budget = 0.0
             max_budget = 5000.0

        if min_budget < 0: min_budget = 0
        if max_budget <= min_budget: max_budget = min_budget + 500 # Ensure range > 0

        budget_range = max_budget - min_budget
        if price <= min_budget: price_score = 1.0
        elif price > max_budget: price_score = 0.0
        else: price_score = 1.0 - ((price - min_budget) / budget_range) if budget_range > 0 else 0.0
        score += price_score * price_weight
    # else: print("Debug: Price missing for grade calc.") # Optional debug

    # Duration score (using outbound duration)
    duration = flight.get("outbound_duration_minutes")
    if duration is not None:
        max_acceptable_duration = 960 # 16 hours, adjust as needed
        duration_score = max(0.0, (max_acceptable_duration - duration) / max_acceptable_duration) if max_acceptable_duration > 0 else 0.0
        score += duration_score * duration_weight
    # else: print("Debug: Duration missing for grade calc.") # Optional debug

    # Vibe score
    preferred_vibes = traveler.get("preferredVibes", [])
    if isinstance(preferred_vibes, list) and preferred_vibes and isinstance(city_vibes, dict) and city_vibes:
        matches = 0
        valid_preferred_vibes_count = 0
        for vibe in preferred_vibes:
            if isinstance(vibe, str) and vibe in city_vibes:
                 valid_preferred_vibes_count += 1
                 city_vibe_value = city_vibes.get(vibe)
                 # Check for truthy values (1, "1", True, "true", "yes")
                 if str(city_vibe_value).lower() in ["1", "true", "yes"]:
                     matches += 1

        if valid_preferred_vibes_count > 0:
            vibe_score = matches / valid_preferred_vibes_count
            score += vibe_score * vibe_weight
    # else: print("Debug: No vibes/prefs for grade calc.") # Optional debug

    return round(score, 2)

# --- Main Execution Logic ---

def main():
    """Main function to orchestrate the flight fetching and scoring process."""
    # --- 1. Load Data ---
    airports_by_iata = load_airport_data_by_iata(AIRPORTS_CSV)
    user_info = load_user_info(USER_INFO_JSON)
    destinations_input = load_filtered_routes(FILTERED_JSON)

    # --- 2. Get Origin and Dates ---
    travelers = user_info["travelers"]
    origin_city_name = travelers[0].get("startingPoint", "Madrid") # Default if missing
    if not isinstance(origin_city_name, str) or not origin_city_name:
        print("Warning: Invalid startingPoint in first traveler, defaulting to Madrid.")
        origin_city_name = "Madrid"

    # Find IATA for the origin city (still needed)
    origin_iata = find_iata_for_city(origin_city_name, AIRPORTS_CSV)
    if not origin_iata:
        print(f"CRITICAL Error: Could not determine IATA code for origin city '{origin_city_name}'. Please check the city name or CSV data. Exiting.")
        # You could fallback to a default like "MAD" here if acceptable:
        # print("Warning: Falling back to 'MAD' as origin IATA.")
        # origin_iata = "MAD"
        exit() # Safer to exit if origin is unknown

    date_range = user_info["dateRange"]
    try:
        departure_date = datetime.fromisoformat(date_range["startDate"]).date()
        # Handle optional return date
        return_date_str = date_range.get("endDate")
        return_date = datetime.fromisoformat(return_date_str).date() if return_date_str else None
        print(f"Using Departure: {departure_date}, Return: {return_date if return_date else 'One-way'}")
    except (ValueError, TypeError, KeyError) as e:
        print(f"CRITICAL Error parsing dates from user info: {e}. Check 'dateRange' format. Exiting.")
        exit()

    # --- 3. Process Each Destination ---
    enriched_destinations = []
    total_destinations = len(destinations_input)
    print(f"\nStarting flight search for {total_destinations} destinations from {origin_iata}...")

    for index, dest_data in enumerate(destinations_input):
        city_name = dest_data.get("city", "Unknown City")
        # *** Get IATA directly from input ***
        destination_iata = dest_data.get("iata")

        print(f"\nProcessing destination {index + 1}/{total_destinations}: {city_name} (Input IATA: {destination_iata})...")

        # Validate input IATA
        if not destination_iata or not isinstance(destination_iata, str) or len(destination_iata) != 3:
            print(f"Warning: Invalid or missing IATA code '{destination_iata}' for city '{city_name}' in input file. Skipping.")
            dest_data["flight_score"] = 0
            dest_data["traveler_scores"] = []
            dest_data["note"] = f"Invalid/Missing IATA in input: {destination_iata}"
            enriched_destinations.append(dest_data)
            continue

        # Get vibes using the validated IATA
        airport_info = airports_by_iata.get(destination_iata, {})
        city_vibes = airport_info.get('vibes', {})
        if not city_vibes:
            # print(f"Debug: No vibe data found for IATA {destination_iata}") # Optional debug
            pass
        dest_data["city_vibes"] = city_vibes # Add vibes to output data

        # Search for flights
        session_token = None
        poll_data = None
        flights = []
        api_error_note = None
        try:
            session_token = create_session(origin_iata, destination_iata, departure_date, return_date)
            if session_token:
                poll_data = poll_results(session_token) # Can return None on failure
                if poll_data:
                    flights = extract_flight_data(poll_data)
                else:
                    api_error_note = "Polling failed or timed out"
            else:
                # Error logged in create_session
                api_error_note = f"Failed to create flight session (API rejected IATA?)"

        except Exception as e:
            # Catch unexpected errors during API interaction/processing
            print(f"Error processing flights for {city_name} ({destination_iata}): {str(e)}")
            api_error_note = f"Runtime error during search: {type(e).__name__}"


        # --- 4. Score and Record Results ---
        if flights:
            best_flight = flights[0] # Cheapest flight
            dest_data.update(best_flight) # Add flight details to the dict
            print(f"Best flight found: €{best_flight.get('price_eur', 'N/A')}, {best_flight.get('outbound_airline', 'N/A')}")

            total_score = 0.0
            traveler_scores = []
            for i, traveler in enumerate(travelers):
                 traveler_num = traveler.get("travelerNumber", f"T{i+1}")
                 score = compute_grade(best_flight, traveler, city_vibes)
                 traveler_scores.append({"travelerNumber": traveler_num, "score": score})
                 total_score += score

            avg_score = round(total_score / len(travelers), 2) if travelers else 0.0
            dest_data["flight_score"] = avg_score
            dest_data["traveler_scores"] = traveler_scores
            dest_data["note"] = "Flight found"
            print(f"Average flight score: {avg_score}")

        else:
            # No flights found or API error occurred
            dest_data["flight_score"] = 0
            dest_data["traveler_scores"] = []
            dest_data["note"] = api_error_note if api_error_note else "No flights found"
            print(f"Note: {dest_data['note']}")


        enriched_destinations.append(dest_data)
        # Rate limiting delay
        sleep_duration = 1.5 # Adjust as needed (1.5-2 seconds is often safe)
        # print(f"Sleeping for {sleep_duration} seconds...") # Optional debug
        sleep(sleep_duration)

    # --- 5. Finalize and Save ---
    print(f"\nFinished processing all {total_destinations} destinations.")

    # Sort by final flight score (descending)
    enriched_destinations.sort(key=lambda x: x.get("flight_score", 0), reverse=True)

    # Update final rank based on score
    for i, dest in enumerate(enriched_destinations, 1):
        dest["final_rank"] = i # Add a distinct rank based on flight score

    # Save results
    try:
        with open(OUTPUT_JSON, "w", encoding='utf-8') as f:
            json.dump(enriched_destinations, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {OUTPUT_JSON}")
    except Exception as e:
        print(f"Error saving results to {OUTPUT_JSON}: {str(e)}")

    # Print top results summary
    print("\nTop 10 Destinations (based on flight score):")
    rank_count = 0
    for dest in enriched_destinations:
        if rank_count >= 10: break
        # Only show if score > 0 or flight was explicitly noted as found
        if dest.get("flight_score", 0) > 0 or "Flight found" == dest.get("note", ""):
            price = f"€{dest.get('price_eur', 'N/A')}" if dest.get('price_eur') is not None else "N/A"
            print(f"Rank {dest.get('final_rank', 'N/A')}. {dest.get('city', 'N/A')} ({dest.get('iata', 'N/A')}) "
                  f"- Score: {dest.get('flight_score', 0)}, Price: {price}, Note: {dest.get('note', 'OK')}")
            rank_count += 1
        # Optionally print failures too for debugging:
        # else:
        #     print(f"Rank {dest.get('final_rank', 'N/A')}. {dest.get('city', 'N/A')} ({dest.get('iata', 'N/A')}) "
        #           f"- Score: {dest.get('flight_score', 0)}, Note: {dest.get('note', 'Error')}")
        #     rank_count +=1


if __name__ == "__main__":
    main()