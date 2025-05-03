import os
import json
import sqlite3
import requests
from datetime import datetime
from time import sleep

# Configuration
API_KEY = os.getenv('API_KEY')  # Ensure this environment variable is set
CREATE_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create"
POLL_URL = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/poll"

HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

DATA_DIR = "data"
FILTERED_ROUTES_FILE = os.path.join(DATA_DIR, "filtered_routes.txt")
API_CACHE_DB = os.path.join(DATA_DIR, "api_cache.db")

def read_filtered_routes(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def create_search_session(origin, destination, departure_date):
    payload = {
        "query": {
            "market": "ES",
            "locale": "en-GB",
            "currency": "EUR",
            "queryLegs": [
                {
                    "originPlace": {"iata": origin},
                    "destinationPlace": {"iata": destination},
                    "date": {"year": departure_date.year, "month": departure_date.month, "day": departure_date.day}
                }
            ],
            "cabinClass": "CABIN_CLASS_ECONOMY",
            "adults": 1
        }
    }
    response = requests.post(CREATE_URL, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()["sessionToken"]

def poll_search_results(session_token):
    url = f"{POLL_URL}/{session_token}"
    for _ in range(10):  # Retry up to 10 times
        response = requests.post(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "UpdatesComplete":
            return data
        sleep(1)  # Wait before retrying
    raise Exception("Polling timed out.")

def store_results(db_path, origin, destination, departure_date, results):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            origin TEXT,
            destination TEXT,
            departure_date TEXT,
            price REAL,
            airline TEXT,
            flight_number TEXT,
            departure_time TEXT,
            arrival_time TEXT
        )
    ''')
    for itinerary in results.get("itineraries", []):
        price = itinerary.get("pricingOptions", [{}])[0].get("price", {}).get("amount")
        for leg in itinerary.get("legs", []):
            airline = leg.get("carriers", [{}])[0].get("name")
            flight_number = leg.get("flightNumbers", [{}])[0].get("flightNumber")
            departure_time = leg.get("departure")
            arrival_time = leg.get("arrival")
            cursor.execute('''
                INSERT INTO flights (origin, destination, departure_date, price, airline, flight_number, departure_time, arrival_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (origin, destination, departure_date.isoformat(), price, airline, flight_number, departure_time, arrival_time))
    conn.commit()
    conn.close()

def main():
    routes = read_filtered_routes(FILTERED_ROUTES_FILE)
    departure_date = datetime(2025, 5, 14)  # Example departure date
    for destination in routes:
        origin = "MAD"  # Example origin; replace with actual data
        try:
            print(f"Processing route: {origin} -> {destination}")
            session_token = create_search_session(origin, destination, departure_date)
            results = poll_search_results(session_token)
            store_results(API_CACHE_DB, origin, destination, departure_date, results)
        except Exception as e:
            print(f"Error processing route {origin} -> {destination}: {e}")

if __name__ == "__main__":
    main()
