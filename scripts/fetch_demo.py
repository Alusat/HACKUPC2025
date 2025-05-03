import requests
import json
import argparse
import sys
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


def search_flights(api_key: str) -> Optional[Dict[str, Any]]:
    """
    Search for indicative flight prices using Skyscanner API.

    Args:
        api_key (str): Your Skyscanner API key

    Returns:
        Optional[Dict[str, Any]]: The JSON response from the API or None if the request fails
    """
    # API endpoint
    url: str = "https://partners.api.skyscanner.net/apiservices/v3/flights/indicative/search"

    # Headers
    headers: Dict[str, str] = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    # Request payload
    payload: Dict[str, Any] = {
        "query": {
            "market": "ES",
            "locale": "en-GB",
            "currency": "EUR",
            "queryLegs": [
                {
                    "originPlace": {
                        "queryPlace": {
                            "iata": "BCN"
                        }
                    },
                    "destinationPlace": {
                        "queryPlace": {
                            "iata": "JFK"
                        }
                    },
                    "anytime": True
                }
            ]
        }
    }

    try:
        # Make the POST request
        response: requests.Response = requests.post(url, headers=headers, json=payload)

        # Check if the request was successful
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {response.text if 'response' in locals() else 'No response'}")
    except requests.exceptions.ConnectionError as e:
        print(f"Connection Error: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Timeout Error: {e}")
    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")

    return None


def main() -> None:
    # Load environment variables from .env file
    load_dotenv()

    # get API key from environment variable
    api_key: str = os.getenv("API_KEY")

    # Search for flights
    results: Optional[Dict[str, Any]] = search_flights(api_key)

    # Print results (if successful)
    if results:
        print(json.dumps(results, indent=4))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()