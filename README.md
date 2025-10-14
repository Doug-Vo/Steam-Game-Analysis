# Steam Recent Reviews Data Pipeline

## Project Objective

This is a data engineering project designed to build a comprehensive and up-to-date dataset of Steam games and their recent user reviews. The pipeline acquires data from multiple sources (Steam API, SteamSpy API) and stores it in a structured MongoDB database.

The ultimate goal of this project is to use the collected data to perform sentiment analysis and create a custom "Recent Review Score" for each game.

## Current Status

This project is currently in the initial development phase.

- **Completed:**
  - Project structure has been set up.
  - Version control (`Git`) and task management (`Jira`) workflows are established.
  - A reusable logging module (`log_debug.py`) has been created.
  - The initial database connection module is complete.

- **In Progress:**
  - Phase 1: Building the data acquisition pipeline for the `games` collection.

## Tech Stack

- **Language:** Python
- **Database:** MongoDB Atlas
- **Core Libraries:**
  - `requests` (for API calls)
  - `pymongo` (for database interaction)
  - `colorama` (for colored logging)
- **Future Libraries:** `pandas`, `vaderSentiment`

## How to Set Up

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Doug-Vo/Steam-Game-Analysis.git
    cd Steam-Game-Analysis
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    py -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    - This project requires a MongoDB Atlas connection string. Set it as an environment variable named `MONGO_URI`.

## Project Roadmap

-   [ ] **Phase 1: Game Metadata Ingestion:** Build the `ingest_games.py` script to populate the `games` collection by fusing data from the Steam and SteamSpy APIs.
-   [ ] **Phase 2: Review Ingestion:** Build the `ingest_reviews.py` script to scrape recent reviews for all games in the database and store them in the `reviews` collection.
-   [ ] **Phase 3: Sentiment Analysis:** Develop a script to process the raw review text, calculate a "Recent Review Score" for each game, and save the final, analyzed dataset.