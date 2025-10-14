import log_debug
from pymongo import MongoClient
import os
import sys

MONGO_URI = os.environ.get('MONGO_URI')

client = MongoClient(MONGO_URI)

DB_NAME = "steam_games"
COLLECTION_NAME = "game_infos"

collection = client[DB_NAME][COLLECTION_NAME]

try:
    client.admin.command('ping')
    log_debug.logging.info("MongoDB connection succesful") 
    

except Exception as e:
    log_debug.logging.error(f"UNABLE TO connect to mongoDB: {e}")


