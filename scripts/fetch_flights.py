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

# Using the INDICATIVE API endpoint instead of the live search
INDICATIVE_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/indicative/search"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# File paths
FILTERED_JSON = "data/ranked_cities_top100.json"
OUTPUT_JSON = "data/enriched_routes.json"
AIRPORTS_CSV = "data/iata_airports_and_locations_with_vibes.csv"
USER_INFO_JSON = "data/user_info.json"

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


# --- Skyscanner API Functions (UPDATED to use Indicative API) ---

def get_indicative_price(origin: str, destination: str, departure_date: Optional[date] = None, return_date: Optional[date] = None) -> Optional[Dict]:
    """Get indicative flight prices from Skyscanner's Indicative API.
    
    This is much faster than live search as it returns cached prices.
    If departure_date is None, it will search for "anytime" flights.
    """
    query = {
        "market": "ES",  # Assuming Spain market
        "locale": "en-GB",
        "currency": "EUR",
        "queryLegs": [
            {
                "originPlace": {
                    "queryPlace": {"iata": origin}
                },
                "destinationPlace": {
                    "queryPlace": {"iata": destination}
                }
            },
            {
                "originPlace": {
                    "queryPlace": {"iata": destination}
                },
                "destinationPlace": {
                    "queryPlace": {"iata": origin}
                }
            }
        ]
    }
    
    # Add date if specified, otherwise use "anytime" parameter
    if departure_date and return_date:
        print(f"hay dates: {departure_date} and {return_date}")
        query["queryLegs"][0]["fixedDate"] = {
            "year": departure_date.year,
            "month": departure_date.month,
            "day": departure_date.day
        }
        query["queryLegs"][1]["fixedDate"] = {
            "year": return_date.year,
            "month": return_date.month,
            "day": return_date.day
        }
    else:
        print("WARNING: No dates provided, searching for 'anytime' flights. ONLY ONE WAY FLIGHT.")
        query["queryLegs"][0]["anytime"] = True       # Delete the second leg if no return date is provided
        del query["queryLegs"][1] # Delete the second leg if no return date is provided 

    
    payload = {"query": query}
    print(f"Getting indicative price: {origin} -> {destination} {'on ' + str(departure_date) if departure_date else 'anytime'}")
    
    try:
        res = requests.post(INDICATIVE_URL, headers=HEADERS, json=payload, timeout=10)
        print(f"Indicative API response status code for {destination}: {res.status_code}")
        
        if res.status_code != 200:
            print(f"Error getting indicative price for {destination}: Status Code {res.status_code}")
            error_details = {}
            try:
                error_details = res.json()
                print(f"API Error Response: {json.dumps(error_details, indent=2)}")
            except json.JSONDecodeError:
                print(f"API Error Response (non-JSON): {res.text}")
            # Check for specific invalid IATA error
            if "QueryPlace ID is not valid IATA" in str(error_details) or "INVALID_PLACE" in str(error_details):
                print(f"*** API rejected IATA code '{destination}'. Please verify the IATA in the input file '{FILTERED_JSON}'. ***")
            return None
        
        response_json = res.json()
        print(f"Indicative API response for {destination}: {json.dumps(response_json, indent=2)}")

        return response_json
        
    except requests.exceptions.Timeout:
        print(f"Error getting indicative price for {destination}: Request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error getting indicative price for {destination}: Request failed: {str(e)}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred getting indicative price for {destination}: {str(e)}")
        return None

# --- Flight Data Extraction Function ---
def extract_indicative_flight_data(indicative_data: Dict) -> Optional[Dict]:
    """
    Extracts flight details from the indicative search response.
    Ahora navega a content.results.quotes en lugar de buscar quotes arriba.
    """
    # Asegurarnos de que tenemos el bloque esperado
    content = indicative_data.get("content", {})
    results = content.get("results", {})
    
    quotes_dict = results.get("quotes", {})
    if not isinstance(quotes_dict, dict) or not quotes_dict:
        print("No quotes found in content.results.quotes.")
        return None

    # Tomamos la cotización más barata
    try:
        cheapest_quote = min(
            quotes_dict.values(),
            key=lambda q: float(q.get("minPrice", {}).get("amount", float("inf")))
        )
    except (ValueError, TypeError):
        print("Warning: Could not find valid price in quotes.")
        return None

    carriers = results.get("carriers", {})
    places   = results.get("places", {})

    # Precio
    price_str = cheapest_quote.get("minPrice", {}).get("amount")
    if price_str is None:
        return None
    price = float(price_str)
    if price > 10000:
        price /= 1000.0
    price = round(price, 2)

    # Carrier (aerolínea)
    outbound = cheapest_quote.get("outboundLeg", {})
    carrier_id = outbound.get("marketingCarrierId")
    carrier_name = carriers.get(carrier_id, {}).get("name", "Unknown Airline") if carrier_id else "Unknown Airline"

    # Aeropuertos origen/destino
    origin_id      = outbound.get("originPlaceId")
    destination_id = outbound.get("destinationPlaceId")
    origin_code      = places.get(origin_id, {}).get("iata", "Unknown") if origin_id else "Unknown"
    destination_code = places.get(destination_id, {}).get("iata", "Unknown") if destination_id else "Unknown"

    # Construimos el dict simplificado
    flight = {
        "price_eur": price,
        "outbound_airline": carrier_name,
        "outbound_origin_airport": origin_code,
        "outbound_destination_airport": destination_code,
        # Note: La API indicativa no da tiempos exactos, pero si quieres podrías usar groupingOptions:
        "outbound_departure_time": None,
        "outbound_arrival_time": None,
        "outbound_duration_minutes": None,
        # Para simetría, dejamos campos de vuelta
        "return_airline": None,
        "return_origin_airport": None,
        "return_destination_airport": None,
        "return_departure_time": None,
        "return_arrival_time": None,
        "return_duration_minutes": None,
    }
    return flight

# --- Scoring Function --- (Unchanged)
def compute_grade(flight: Dict, traveler: Dict, city_vibes: Dict) -> float:
    """Computes a score for a flight based on traveler preferences and city vibes."""
    score = 0.0
    price_weight = 5.0
    duration_weight = 1.0  # Reduced from 3.0 since we don't have duration in indicative results
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

    # Duration score - not available in indicative data, use a default mid-range score
    # We could remove this entirely, but keeping a neutral score helps maintain relative weighting
    score += 0.5 * duration_weight  # Default middle score for duration

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

    return round(score, 2)

# --- Main Execution Logic ---

def main():
    """Main function to orchestrate the flight fetching and scoring process using the Indicative API."""
    # --- 1. Load Data ---
    airports_by_iata = load_airport_data_by_iata(AIRPORTS_CSV)
    user_info = load_user_info(USER_INFO_JSON)
    destinations_input = load_filtered_routes(FILTERED_JSON)

    # --- 2. Get Origin and Dates ---
    travelers = user_info["travelers"]
    origin_city_name = travelers[0].get("startingPoint", "Default") # Default if missing
    if not isinstance(origin_city_name, str) or not origin_city_name:
        print("Warning: Invalid startingPoint in first traveler, defaulting to Madrid.")
        origin_city_name = "Madrid"

    # Find IATA for the origin city
    origin_iata = find_iata_for_city(origin_city_name, AIRPORTS_CSV)
    if not origin_iata:
        print(f"CRITICAL Error: Could not determine IATA code for origin city '{origin_city_name}'. Please check the city name or CSV data. Exiting.")
        exit()

    date_range = user_info["dateRange"]
    try:
        departure_date = datetime.fromisoformat(date_range["startDate"]).date()
        print(f"Using Departure: {departure_date}")
        return_date = datetime.fromisoformat(date_range["endDate"]).date() 
        print(f"Using Return: {return_date}")
        if return_date < departure_date:
            print(f"CRITICAL Error: Return date {return_date} is before departure date {departure_date}. Exiting.")
            exit()
    except (ValueError, TypeError, KeyError) as e:
        print(f"CRITICAL Error parsing dates from user info: {e}. Check 'dateRange' format. Exiting.")
        exit()

    # --- 3. Process Each Destination ---
    enriched_destinations = []
    total_destinations = len(destinations_input)
    print(f"\nStarting indicative flight search for {total_destinations} destinations from {origin_iata}...")
    
    # Track successful and failed searches
    success_count = 0
    failure_count = 0

    for index, dest_data in enumerate(destinations_input):
        city_name = dest_data.get("city", "Unknown City")
        destination_iata = dest_data.get("iata")

        print(f"\nProcessing destination {index + 1}/{total_destinations}: {city_name} (Input IATA: {destination_iata})...")

        # Validate input IATA
        if not destination_iata or not isinstance(destination_iata, str) or len(destination_iata) != 3:
            print(f"Warning: Invalid or missing IATA code '{destination_iata}' for city '{city_name}' in input file. Skipping.")
            dest_data["flight_score"] = 0
            dest_data["traveler_scores"] = []
            dest_data["note"] = f"Invalid/Missing IATA in input: {destination_iata}"
            enriched_destinations.append(dest_data)
            failure_count += 1
            continue

        # Get vibes using the validated IATA
        airport_info = airports_by_iata.get(destination_iata, {})
        city_vibes = airport_info.get('vibes', {})
        dest_data["city_vibes"] = city_vibes # Add vibes to output data
        # Get indicative flight prices
        indicative_data = None
        flight = None
        api_error_note = None
        
        try:
            # 1) Attempt date‐specific search
            indicative_data = get_indicative_price(origin_iata, destination_iata, departure_date, return_date)

            # 2) Drill down to the actual quotes dict
            results = (indicative_data or {}) \
                    .get("content", {}) \
                    .get("results", {})

            quotes = results.get("quotes", {})

            # 3) If no date‐specific quotes, fallback to anytime
            if not quotes:
                print(f"No quotes found for specific date, trying anytime search for {destination_iata}...")
                indicative_data = get_indicative_price(origin_iata, destination_iata, None)
                results = (indicative_data or {}) \
                        .get("content", {}) \
                        .get("results", {})
                quotes = results.get("quotes", {})

            # 4) If we finally have quotes, extract; otherwise record no‐data
            if quotes:
                flight = extract_indicative_flight_data(indicative_data)
            else:
                api_error_note = "No indicative prices available"

                
        except Exception as e:
            print(f"Error processing indicative prices for {city_name} ({destination_iata}): {str(e)}")
            api_error_note = f"Runtime error during search: {type(e).__name__}"

        # --- 4. Score and Record Results ---
        if flight:
            dest_data.update(flight) # Add flight details to the dict
            print(f"Found indicative price: €{flight.get('price_eur', 'N/A')}, {flight.get('outbound_airline', 'N/A')}")

            total_score = 0.0
            traveler_scores = []
            for i, traveler in enumerate(travelers):
                 traveler_num = traveler.get("travelerNumber", f"T{i+1}")
                 score = compute_grade(flight, traveler, city_vibes)
                 traveler_scores.append({"travelerNumber": traveler_num, "score": score})
                 total_score += score

            avg_score = round(total_score / len(travelers), 2) if travelers else 0.0
            dest_data["flight_score"] = avg_score
            dest_data["traveler_scores"] = traveler_scores
            dest_data["note"] = "Indicative price found"
            print(f"Average flight score: {avg_score}")
            success_count += 1
        else:
            # No flights found or API error occurred
            dest_data["flight_score"] = 0
            dest_data["traveler_scores"] = []
            dest_data["note"] = api_error_note if api_error_note else "No indicative prices found"
            print(f"Note: {dest_data.get('note', 'No flight data')}")
            failure_count += 1

        enriched_destinations.append(dest_data)
        
        # Very small rate limiting delay (can be reduced further since indicative API is less rate-limited)
        sleep_duration = 0.2  # Much shorter than before
        sleep(sleep_duration)

    # --- 5. Finalize and Save ---
    print(f"\nFinished processing all {total_destinations} destinations.")
    print(f"Success: {success_count}, Failed: {failure_count}")

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
        if dest.get("flight_score", 0) > 0 or "price found" in dest.get("note", "").lower():
            price = f"€{dest.get('price_eur', 'N/A')}" if dest.get('price_eur') is not None else "N/A"
            print(f"Rank {dest.get('final_rank', 'N/A')}. {dest.get('city', 'N/A')} ({dest.get('iata', 'N/A')}) "
                  f"- Score: {dest.get('flight_score', 0)}, Price: {price}, Note: {dest.get('note', 'OK')}")
            rank_count += 1

if __name__ == "__main__":
    main()