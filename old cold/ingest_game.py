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
import re
from pymongo import MongoClient
from tqdm import tqdm

# Imports the custom logger
from api_clients.steam_api_clients import get_steamspy_game, fetch_steam_reviews
from utility.log_debug import logging
from pymongo.operations import UpdateOne
import time 
import random
from concurrent.futures import ThreadPoolExecutor


# --- CONFIGURATION & SETUP ---

MONGO_URI = os.environ.get('MONGO_URI')

client = MongoClient(MONGO_URI)

DB_NAME = "steam_games"
GAME_COLLECTION = "game_infos"
REVIEW_COLLECTION = "reviews"

MAX_WORKERS = 15

game_collection = client[DB_NAME][GAME_COLLECTION]
review_collection = client[DB_NAME][REVIEW_COLLECTION]

STEAMSPY_API_URL = "https://steamspy.com/api.php?request=all"

# --- DATABASE CONNECTION TEST ---
try:
    client.admin.command('ping')
    logging.info("MongoDB connection successful.")
except Exception as e:
    logging.error(f"UNABLE to connect to MongoDB. Please check your MONGO_URI. Error: {e}")
    sys.exit(1)


def process_review(app_id):
    try:
        reviews = fetch_steam_reviews(app_id)
        if reviews:
            bulk_op = []
            for single_review in reviews:
                query = {"recommendationid" : single_review["recommendationid"]}
                operation = {"$set": single_review}
                bulk_op.append(UpdateOne(query, operation, upsert= True))

            if bulk_op:
                review_collection.bulk_write(bulk_op)
    except Exception as e:
        logging.error(f"ERROR, Unable to load {single_review} : {e}")
    return 


# --- MAIN EXECUTION BLOCK ---
if __name__ == "__main__":
    # Step 1: Fetch the master list of all games.
    all_games_data = get_steamspy_game(STEAMSPY_API_URL)

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
                game_collection.update_one(filter_query, update_operation, upsert=True)

            except Exception as e:
                logging.error(f"Unable to process {app_id}: {info_dict.get('name')}. Error: {e}")
                continue



        logging.info("--- COMPLETE LOADING GAME INFO ---")
        logging.info("--- BEGIN TO COLLECT GAME REVIEWS ---")

        
        app_ids = []

        for app_info, info_dict in all_games_data.items():
                app_ids.append(int(app_info))
        
        with ThreadPoolExecutor(max_workers= MAX_WORKERS) as executor:
            list(tqdm(executor.map(process_review, app_ids), total=len(app_ids), desc= "Processing..."))
            
        logging.info("--- COMPLETE LOADING GAME REVIEWS ---")