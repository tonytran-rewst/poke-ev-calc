#!/usr/bin/env python3
"""
Script to fetch Pokémon card data from the Pokémon TCG API,
transform it, and insert into Supabase.
Can be run on a cron schedule to keep the database updated.

Usage:
    python populate_cards.py
"""

import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from pokemontcgsdk import RestClient
from pokemontcgsdk import Card
from pokemontcgsdk import Set

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("update_data.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("update_script")

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # This should be a service key with write access

# PokemonTCG SDK setup
POKEMONTCG_IO_API_KEY = os.getenv('POKEMONTCG_IO_API_KEY')

# Validate configuration
if not SUPABASE_URL or not SUPABASE_KEY:
    logger.error("Missing Supabase configuration. Make sure SUPABASE_URL and SUPABASE_KEY are set.")
    exit(1)

if not POKEMONTCG_IO_API_KEY:
    logger.error("Missing Pokemon TCG API key. Make sure POKEMONTCG_IO_API_KEY is set.")
    exit(1)

def fetch_data_from_api():
    """Fetch Pokémon card data from the Pokémon TCG API"""
    logger.info("Fetching Pokémon card data from the Pokémon TCG API")
    try:
        # Configure the Pokemon TCG SDK with your API key
        #RestClient(POKEMONTCG_IO_API_KEY)
        
        # Get cards from the 'prismatic' set that are Pokémon cards
        cards = Card.all()
        #cards = Card.where(q='set.name:prismatic*evolutions supertype:pokemon')
        #cards = Card.where(q='set.name:"Prismatic*Evolutions" rarity:"Special Illustration Rare"')
        
        logger.info(f"Successfully fetched {len(cards)} Pokémon cards")
        return cards
    except Exception as e:
        logger.error(f"Error fetching data from Pokémon TCG API: {e}")
        return None

def transform_data(cards):
    """Transform the Pokémon card data into the format needed for Supabase"""
    logger.info("Transforming Pokémon card data...")
    
    transformed_data = []
    
    try:
        # Process each Pokémon card
        for card in cards:
            # Extract relevant data from each card
            transformed_item = {
                "id": card.id,
                "card_name": card.name,
                "set_id": card.set.id,
                "set_name": card.set.name,
                "types": json.dumps(card.types) if hasattr(card, 'types') and card.types else None,
                "subtypes": json.dumps(card.subtypes) if hasattr(card, 'subtypes') and card.subtypes else None,
                "supertype": card.supertype,
                "rarity": card.rarity if hasattr(card, 'rarity') else None,
                "card_number": card.number,
                "tcgplayer": {
                    "url": card.tcgplayer.url,
                    "updatedAt": card.tcgplayer.updatedAt,
                    "prices": {
                        "normal": getattr(card.tcgplayer.prices.normal, "market", None),
                        "holofoil": getattr(card.tcgplayer.prices.holofoil, "market", None),
                        "reverseHolofoil": getattr(card.tcgplayer.prices.reverseHolofoil, "market", None),
                        "firstEditionHolofoil": getattr(card.tcgplayer.prices.firstEditionHolofoil, "market", None),
                        "firstEditionNormal": getattr(card.tcgplayer.prices.firstEditionNormal, "market", None),
                    } if hasattr(card, 'tcgplayer.prices') and card.tcgplayer.prices else None,
                } if hasattr(card, 'tcgplayer') and card.tcgplayer else None,
                "artist": card.artist if hasattr(card, 'artist') else None,
                "evolves_from": card.evolvesFrom,
                "image_small": card.images.small if hasattr(card, 'images') and hasattr(card.images, 'small') else None,
                "image_large": card.images.large if hasattr(card, 'images') and hasattr(card.images, 'large') else None,
                "updated_at": datetime.now().isoformat()
            }
            
            transformed_data.append(transformed_item)
            
        logger.info(f"Transformed {len(transformed_data)} Pokémon cards")
        return transformed_data
    except Exception as e:
        logger.error(f"Error transforming Pokémon card data: {e}")
        return []

def insert_into_supabase(data, table_name="pokemon_cards"):
    """Insert the transformed Pokémon card data into Supabase"""
    if not data:
        logger.warning("No Pokémon card data to insert")
        return 0
    
    logger.info(f"Inserting {len(data)} Pokémon cards into Supabase table '{table_name}'")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    endpoint = f"{SUPABASE_URL}/rest/v1/{table_name}"
    
    try:
        # Use upsert to update existing records or insert new ones
        # The 'card_id' field is assumed to be the primary key
        upsert_endpoint = f"{endpoint}?on_conflict=card_id"
        
        response = requests.post(
            upsert_endpoint,
            headers=headers,
            data=json.dumps(data)
        )
        
        if response.status_code == 201:
            logger.info(f"Successfully inserted {len(data)} Pokémon card records")
            return len(data)
        else:
            logger.error(f"Error inserting Pokémon card data: {response.status_code} - {response.text}")
            return 0
    except Exception as e:
        logger.error(f"Exception during Pokémon card data insertion: {e}")
        return 0

def main():
    """Main function to orchestrate the data pipeline"""
    logger.info("Starting data update process")
    
    # Fetch data from the API
    api_data = fetch_data_from_api()
    if not api_data:
        logger.error("Failed to fetch data from API. Exiting.")
        return
    
    # Transform the data
    transformed_data = transform_data(api_data)
    if not transformed_data:
        logger.error("Data transformation resulted in no records. Exiting.")
        return

    # Insert into Supabase
    inserted_count = insert_into_supabase(transformed_data)
    
    logger.info(f"Update process completed. {inserted_count} records inserted.")

if __name__ == "__main__":
    main()