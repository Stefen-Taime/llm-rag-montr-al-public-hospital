import os
import logging
from neo4j import GraphDatabase
from dotenv import load_dotenv
from retry import retry

# Load environment variables from .env file
load_dotenv()

# Paths to CSV files containing hospital data
HOSPITALS_CSV_PATH = os.getenv("HOSPITALS_CSV_PATH")
PATIENTS_CSV_PATH = os.getenv("PATIENTS_CSV_PATH")
VISITS_CSV_PATH = os.getenv("VISITS_CSV_PATH")
REVIEWS_CSV_PATH = os.getenv("REVIEWS_CSV_PATH")

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
LOGGER = logging.getLogger(__name__)

# Set of node types
NODES = ["Hospital", "Patient", "Visit", "Review"]

def set_uniqueness_constraints(tx, node):
    query = f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node}) REQUIRE n.id IS UNIQUE"
    result = tx.run(query)
    LOGGER.info(f"Set uniqueness constraint for {node}: {result.consume().counters}")

@retry(tries=3, delay=2)
def load_hospital_graph_from_csv():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

    with driver.session() as session:
        # Setting uniqueness constraints on nodes
        for node in NODES:
            session.write_transaction(set_uniqueness_constraints, node)

        # Loading nodes and relationships
        load_nodes(session)
        create_relationships(session)

def load_nodes(session):
    # Load hospitals
    load_hospitals(session)
    # Load patients
    load_patients(session)
    # Load visits
    load_visits(session)
    # Load reviews
    load_reviews(session)

def load_hospitals(session):
    query = f"""
    LOAD CSV WITH HEADERS FROM '{HOSPITALS_CSV_PATH}' AS row
    MERGE (h:Hospital {{id: toInteger(row.hospital_id)}})
    SET h += {{
        name: row.hospital_name, description: row.description,
        Address: row.Address, Served_Areas: row.Served_Areas, Hours: row.Hours,
        Emergencies: row.Emergencies, Phone: row.Phone, Established: row.Established,
        Number_of_Beds: row.Number_of_Beds, Province: row.Province, Function: row.Function,
        Floors: row.Floors, Opening_Date: row.Opening_Date, Building_Height: row.Building_Height,
        Founder: coalesce(row.Founder, "Unknown")
    }};
    """
    result = session.run(query)
    LOGGER.info(f"Loaded hospitals: {result.consume().counters}")

def load_patients(session):
    query = f"""
    LOAD CSV WITH HEADERS FROM '{PATIENTS_CSV_PATH}' AS row
    MERGE (p:Patient {{id: toInteger(row.patient_id)}})
    SET p.admission_date = coalesce(row.date_of_admission, 'Unknown');
    """
    result = session.run(query)
    LOGGER.info(f"Loaded patients: {result.consume().counters}")

def load_visits(session):
    query = f"""
    LOAD CSV WITH HEADERS FROM '{VISITS_CSV_PATH}' AS row
    MERGE (v:Visit {{id: toInteger(row.visit_id)}})
    ON CREATE SET v.hospital_id = toInteger(row.hospital_id),
                  v.patient_id = toInteger(row.patient_id),
                  v.admission_date = coalesce(row.date_of_admission, 'Unknown');
    """
    result = session.run(query)
    LOGGER.info(f"Loaded visits: {result.consume().counters}")

def load_reviews(session):
    query = f"""
    LOAD CSV WITH HEADERS FROM '{REVIEWS_CSV_PATH}' AS row
    MERGE (r:Review {{id: toInteger(row.review_id), visit_id: toInteger(row.visit_id)}})
    ON CREATE SET r.text = coalesce(row.review, 'No review provided')
    ON MATCH SET r.text = coalesce(row.review, 'No review provided');
    """
    result = session.run(query)
    LOGGER.info(f"Loaded reviews: {result.consume().counters}")

def create_relationships(session):
    # Creating AT relationships (Visit AT Hospital)
    create_visit_hospital_relationships(session)
    # Creating HAS relationships (Patient HAS Visit)
    create_patient_visit_relationships(session)
    # Creating WRITES relationships (Visit WRITES Review)
    create_visit_review_relationships(session)

def create_visit_hospital_relationships(session):
    query = """
    MATCH (v:Visit), (h:Hospital {id: v.hospital_id})
    MERGE (v)-[:AT]->(h);
    """
    result = session.run(query)
    LOGGER.info(f"Created Visit-Hospital relationships: {result.consume().counters}")

def create_patient_visit_relationships(session):
    query = """
    MATCH (p:Patient), (v:Visit {patient_id: p.id})
    MERGE (p)-[:HAS]->(v);
    """
    result = session.run(query)
    LOGGER.info(f"Created Patient-Visit relationships: {result.consume().counters}")

def create_visit_review_relationships(session):
    query = """
    MATCH (v:Visit), (r:Review {visit_id: v.id})
    MERGE (v)-[:WRITES]->(r);
    """
    result = session.run(query)
    LOGGER.info(f"Created Visit-Review relationships: {result.consume().counters}")

if __name__ == "__main__":
    load_hospital_graph_from_csv()
