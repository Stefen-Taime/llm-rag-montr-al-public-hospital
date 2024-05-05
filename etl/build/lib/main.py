import googlemaps 
import pandas as pd
import os
import logging
from retry import retry
from neo4j import GraphDatabase


# Neo4j config
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# Configure the logging module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

gmaps = GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

place_name = 'The Fab'
place_details = gmaps.places(place_name) 
place_details
