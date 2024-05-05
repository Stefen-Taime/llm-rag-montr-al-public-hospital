import os
from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

HOSPITAL_QA_MODEL = os.getenv("HOSPITAL_QA_MODEL")
HOSPITAL_CYPHER_MODEL = os.getenv("HOSPITAL_CYPHER_MODEL")

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
)

graph.refresh_schema()

cypher_generation_template = """
Task:
Generate Cypher query for a Neo4j graph database.

Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

Note:
Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything other than
for you to construct a Cypher statement. Do not include any text except
the generated Cypher statement. Make sure the direction of the relationship is
correct in your queries. Make sure you alias both entities and relationships
properly. Do not run any queries that would add to or delete from
the database. Make sure to alias all statements that follow as with
statement (e.g. WITH v as visit, c.billing_amount as billing_amount)
If you need to divide numbers, make sure to
filter the denominator to be non zero.


Examples:
# Quel est hopital qui a fait objet du plus grand nombre de critiques au cours de année écoulée ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WHERE v.admission_date <> "Unknown" AND date(v.admission_date) >= date("2020-01-01") AND date(v.admission_date) < date("2024-01-01")
RETURN h.name AS hospital_name, COUNT(r) AS number_of_reviews
ORDER BY number_of_reviews DESC
LIMIT 1;


# Quel est hôpital qui a fait objet du plus grand nombre de critiques au cours de année écoulée ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WHERE v.admission_date <> "Unknown" AND date(v.admission_date) >= date("2020-01-01") AND date(v.admission_date) < date("2024-01-01")
RETURN h.name AS hospital_name, COUNT(r) AS number_of_reviews
ORDER BY number_of_reviews ASC
LIMIT 1;


# Quels sont les 5 hôpitaux ayant le plus grand nombre de lits ?
MATCH (h:Hospital)
RETURN h.name, h.Number_of_Beds AS num_beds
ORDER BY num_beds DESC
LIMIT 5;

# Quels sont les 3 hôpitaux les plus anciens ?
MATCH (h:Hospital)
RETURN h.name, h.Established AS year_established
ORDER BY year_established ASC
LIMIT 3;

# Quels sont les 3 patients ayant le plus grand nombre de visites enregistrées ?
MATCH (p:Patient)-[:HAS]->(v:Visit)
RETURN p.id AS patient_id, COUNT(v) AS num_visits
ORDER BY num_visits DESC
LIMIT 3;

# Quels sont les 3 hôpitaux ayant le plus grand nombre de revues négatives contenant les mots mauvais ou terrible ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WHERE toLower(r.text) CONTAINS "mauvais" OR toLower(r.text) CONTAINS "terrible"
RETURN h.name AS hospital_name, COUNT(r) AS num_negative_reviews
ORDER BY num_negative_reviews DESC
LIMIT 3;

# Quelle est la province ayant le plus grand nombre de visites ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)
RETURN h.Province AS province, COUNT(v) AS num_visits
ORDER BY num_visits DESC;

# Quels sont les hôpitaux avec le nombre moyen de revues par visite le plus élevé ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WITH h, COUNT(r) AS num_reviews, COUNT(DISTINCT v) AS num_visits
WHERE num_visits > 0
RETURN h.name AS hospital_name, toFloat(num_reviews) / num_visits AS avg_reviews_per_visit
ORDER BY avg_reviews_per_visit DESC
LIMIT 3;



# Trouver les hôpitaux ayant le plus grand écart entre le nombre de revues positives et négatives ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WITH h, r,
     CASE
       WHEN toLower(r.text) CONTAINS "bien" OR toLower(r.text) CONTAINS "excellent" THEN 1
       WHEN toLower(r.text) CONTAINS "mauvais" OR toLower(r.text) CONTAINS "terrible" THEN -1
       ELSE 0
     END AS review_sentiment
RETURN h.name AS hospital_name,
       SUM(CASE WHEN review_sentiment = 1 THEN 1 ELSE 0 END) AS positive_reviews,
       SUM(CASE WHEN review_sentiment = -1 THEN 1 ELSE 0 END) AS negative_reviews,
       ABS(SUM(review_sentiment)) AS review_sentiment_gap
ORDER BY review_sentiment_gap DESC
LIMIT 3;


# Quels sont les 3 hôpitaux ayant le plus grand nombre de revues positives contenant les mots excellent ou incroyable ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WHERE toLower(r.text) CONTAINS "excellent" OR toLower(r.text) CONTAINS "incroyable"
RETURN h.name AS hospital_name, COUNT(r) AS num_positive_reviews
ORDER BY num_positive_reviews DESC
LIMIT 3;


# Quels sont les 3 hôpitaux ayant le plus grand nombre de revues neutres ne contenant pas les mots mauvais, terrible, bien ou excellent ?
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WHERE NOT (toLower(r.text) CONTAINS "mauvais" OR toLower(r.text) CONTAINS "terrible" OR toLower(r.text) CONTAINS "bien" OR toLower(r.text) CONTAINS "excellent")
RETURN h.name AS hospital_name, COUNT(r) AS num_neutral_reviews
ORDER BY num_neutral_reviews DESC
LIMIT 3;

# Trouver les hôpitaux ayant reçu des critiques pour les mêmes motifs fréquemment 
MATCH (h:Hospital)<-[:AT]-(v:Visit)-[:WRITES]->(r:Review)
WITH h, r.text AS review, COUNT(*) AS count
WHERE count > 5
RETURN h.name AS hospital_name, review, count
ORDER BY count DESC;

Be sure to use IS NULL or IS NOT NULL when analyzing missing properties.
Never return integration properties in your queries. Never include the
GROUP BY" statement in your query. Be sure to give an alias to all statements that
instructions (e.g. WITH v as visit).
If you need to divide numbers, be sure to filter the denominator so that it's non-zero.
zero.


The question is:
{question}
"""

cypher_generation_prompt = PromptTemplate(
    input_variables=["schema", "question"], template=cypher_generation_template
)

qa_generation_template = """You are an assistant that takes the results
from a Neo4j Cypher query and forms a human-readable response. The
query results section contains the results of a Cypher query that was
generated based on a users natural language question. The provided
information is authoritative, you must never doubt it or try to use
your internal knowledge to correct it. Make the answer sound like a
response to the question.

Query Results:
{context}

Question:
{question}

If the provided information is empty, say you don't know the answer.
Empty information looks like this: []

If the information is not empty, you must provide an answer using the
results. If the question involves a time duration, assume the query
results are in units of days unless otherwise specified.

When names are provided in the query results, such as hospital names,
beware  of any names that have commas or other punctuation in them.
For instance, 'Jones, Brown and Murray' is a single hospital name,
not multiple hospitals. Make sure you return any list of names in
a way that isn't ambiguous and allows someone to tell what the full
names are.

Never say you don't have the right information if there is data in
the query results. Make sure to show all the relevant query results
if you're asked.

Helpful Answer:
"""

qa_generation_prompt = PromptTemplate(
    input_variables=["context", "question"], template=qa_generation_template
)

hospital_cypher_chain = GraphCypherQAChain.from_llm(
    cypher_llm=ChatOpenAI(model=HOSPITAL_CYPHER_MODEL, temperature=0),
    qa_llm=ChatOpenAI(model=HOSPITAL_QA_MODEL, temperature=0),
    graph=graph,
    verbose=True,
    qa_prompt=qa_generation_prompt,
    cypher_prompt=cypher_generation_prompt,
    validate_cypher=True,
    top_k=100,
)