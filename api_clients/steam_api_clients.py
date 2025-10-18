import requests
from log_debug import logging


# --- DATA FETCHING FUNCTION ---
def get_steamspy_game(STEAMSPY_API_URL):
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
    

import requests
import logging
import time
from datetime import datetime, timedelta


def fetch_steam_reviews(appid, num_reviews_target=1000, months_to_fetch=3):
    """
    Fetches up to a target number of reviews from the last N months.
    """

    reviews_collected = []
    cursor = '*'
    
    # Calculate the cutoff date. We will stop when reviews are older than this.
    cutoff_date = datetime.now() - timedelta(days=months_to_fetch * 30)

    while len(reviews_collected) < num_reviews_target:
        try:
            # --- MODIFICATION: Changed the API parameters ---
            # We now ask for 'all' reviews and specify 100 per page.
            url = f"https://store.steampowered.com/appreviews/{appid}?json=1&cursor={cursor}&language=english&filter=all&num_per_page=100"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if not data or data.get("success") != 1 or not data.get("reviews"):
                break
            
            batch_reviews = data.get("reviews", [])
            for review in batch_reviews:
                review_date = datetime.fromtimestamp(review['timestamp_created'])
                if review_date >= cutoff_date:
                    review['app_id'] = appid
                    reviews_collected.append(review)
            
            if batch_reviews:
                last_review_date = datetime.fromtimestamp(batch_reviews[-1]['timestamp_created'])
                if last_review_date < cutoff_date:
                    break

            next_cursor = data.get("cursor")
            if not next_cursor or next_cursor == cursor:
                break
            
            cursor = next_cursor
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            logging.error(f"HTTP Error while fetching reviews for AppID {appid}: {e}")
            break
    return reviews_collected