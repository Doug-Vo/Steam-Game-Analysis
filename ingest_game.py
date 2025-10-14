"""
This script is the first phase of the Steam Data Pipeline.

Its purpose is to:
1. Fetch a master list of all games from the SteamSpy API.
2. Process the data for each game, performing basic cleaning and feature engineering.
3. Store the cleaned data in a MongoDB collection, ensuring no duplicates are created.
"""


# --- IMPORTS ---
import os
import sys
import requests
import re
import log_debug
from pymongo import MongoClient
from tqdm import tqdm

# Imports the custom logger
from log_debug import logging

# --- CONFIGURATION & SETUP ---

MONGO_URI = os.environ.get('MONGO_URI')

client = MongoClient(MONGO_URI)

DB_NAME = "steam_games"
COLLECTION_NAME = "game_infos"

collection = client[DB_NAME][COLLECTION_NAME]

STEAMSPY_API_URL = "https://steamspy.com/api.php?request=all"

# --- DATABASE CONNECTION TEST ---
try:
    client.admin.command('ping')
    logging.info("MongoDB connection successful.")
except Exception as e:
    logging.error(f"UNABLE to connect to MongoDB. Please check your MONGO_URI. Error: {e}")
    sys.exit(1)


# --- DATA FETCHING FUNCTION ---
def get_steamspy_game():
    """Fetches the complete game dataset from the SteamSpy API."""
    try:
        logging.info("Attempting to retrieve data from SteamSpy...")
        response = requests.get(STEAMSPY_API_URL)
        # This will automatically raise an error if the API returns a bad status (e.g., 404, 503).
        response.raise_for_status()
        logging.info("Retrieve data from SteamSpy SUCCESSFULLY!")
        return response.json()
    except Exception as e:
        logging.error(f"Error! Unable to retrieve data from SteamSpy: {e}")
        return None


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # Step 1: Fetch the master list of all games.
    all_games_data = get_steamspy_game()

    # Proceeds only if the API call was successful.
    if all_games_data:
        logging.info(f"Retrieved data for {len(all_games_data)} games. Starting ingestion process...")

        # Step 2: Loop through each game using tqdm to create a progress bar.
        # The .items() method gives us both the appid (key) and the game info (value).
        for app_info, info_dict in tqdm(all_games_data.items(), desc="Processing game data"):
            try:
                app_id = int(app_info)

                # --- Step 3: Feature Engineering for 'owners' ---
                # Safely parse the 'owners' string (e.g., "20,000 .. 50,000") into numbers.
                min_owner = 0  # Initialize with a safe default value.
                max_owner = 0  # Initialize with a safe default value.

                owner_string = info_dict.get("owners")
                if owner_string:
                    # Finds all numbers in the string.
                    owner_numbers = re.findall(r'\d+', owner_string.replace(",", ""))
                    # Checks if we found at least one number to prevent errors.
                    if len(owner_numbers) >= 2:
                        min_owner = int(owner_numbers[0])
                        max_owner = int(owner_numbers[1])
                    elif len(owner_numbers) == 1:
                        # Handles cases where only one number is provided (e.g., "5,000").
                        min_owner = int(owner_numbers[0])
                        max_owner = int(owner_numbers[0])

                # --- Step 4: Create the final document for MongoDB ---
                game_document = {
                    "_id": app_id,  # Use the app_id as the unique primary key.
                    "name": info_dict.get("name"),
                    "developer": info_dict.get("developer"),
                    "publisher": info_dict.get("publisher"),
                    "score_rank": info_dict.get("score_rank"),
                    "positive_reviews": info_dict.get("positive"),
                    "negative_reviews": info_dict.get("negative"),
                    "user_score": info_dict.get("userscore"),
                    "min_owners_estimated": min_owner, # Use the cleaned integer value.
                    "max_owners_estimated": max_owner, # Use the cleaned integer value.
                    "avg_playtime_forever": info_dict.get("average_forever"),
                    "avg_playtime_2weeks": info_dict.get("average_2weeks"),
                    "price_cents": info_dict.get("price"),
                    "initial_price_cents": info_dict.get("initialprice"),
                    "discount_percent": info_dict.get("discount"),
                    "concurrent_users": info_dict.get("ccu"),
                }
                
                # --- Step 5: Upsert the document into the database ---
                filter_query = {"_id": app_id}
                update_operation = {"$set": game_document}

                # If a document with this _id exists, it will be updated.
                # If not, it will be inserted as a new document.
                collection.update_one(filter_query, update_operation, upsert=True)

            except Exception as e:
                logging.error(f"Unable to process {app_id}: {info_dict.get('name')}. Error: {e}")
                continue
        
        logging.info("--- COMPLETE LOADING GAME INFO ---")