import time
import logging
import requests
from kafka_client import produce_message, read_config

# API Setup
from dotenv import load_dotenv
import os

load_dotenv()

# API Setup
SPORTMONKS_API_KEY = "Rd13rLX2LPaUFKOHh2ksjC4thX0si72tJckZIyXU6ic6Dw1RsTMdhkNdhnPg"
SPORTMONKS_LIVE_URL = f"https://api.sportmonks.com/v3/football/livescores/latest?api_token={SPORTMONKS_API_KEY}"

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def fetch_live_soccer_data():
    """Fetch live soccer data from the SportMonks API and produce it to Kafka."""
    try:
        logging.info("Fetching live soccer data from SportMonks API...")
        response = requests.get(SPORTMONKS_LIVE_URL, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        raw_data = response.json()

        # Transform data to match schema
        transformed_data = transform_to_schema(raw_data)

        # Produce each match to Kafka
        kafka_config = read_config(file_path="config/client.properties")
        for match in transformed_data:
            produce_message(
                topic="topic_livescores",
                config=kafka_config,
                key=str(match["id"]),
                value=match
            )
        logging.info(f"Successfully produced {len(transformed_data)} messages to Kafka.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching live soccer data: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


def transform_to_schema(raw_data):
    """Transform raw API data into the desired schema."""
    try:
        matches = raw_data.get("data", [])
        if not matches:
            logging.warning("No matches found in API response.")
            return []

        transformed_data = []

        for match in matches:
            transformed_data.append({
                "id": match.get("id", 0),
                "sport_id": match.get("sport_id", 0),
                "league_id": match.get("league_id", 0),
                "season_id": match.get("season_id", 0),
                "stage_id": match.get("stage_id", 0),
                "group_id": match.get("group_id", None),
                "aggregate_id": match.get("aggregate_id", None),
                "round_id": match.get("round_id", 0),
                "state_id": match.get("state_id", 0),
                "venue_id": match.get("venue_id", 0),
                "name": match.get("name", "Unknown Match"),
                "starting_at": match.get("time", {}).get("starting_at", {}).get("date_time", ""),
                "result_info": match.get("result_info", None),
                "leg": match.get("leg", "first"),
                "details": match.get("details", None),
                "length": match.get("length", 90),
                "placeholder": match.get("placeholder", False),
                "has_odds": match.get("has_odds", False),
                "has_premium_odds": match.get("has_premium_odds", False),
                "starting_at_timestamp": int(time.time()),  # Example: Current timestamp
            })

        return transformed_data

    except KeyError as e:
        logging.error(f"Error transforming data: Missing key {e}")
        return []
    except Exception as e:
        logging.error(f"Unexpected error during transformation: {e}")
        return []


if __name__ == "__main__":
    fetch_live_soccer_data()