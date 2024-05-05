import sys
sys.path.append('/home/stefen/mtl-H')
import dotenv
dotenv.load_dotenv()

from chatbot_api.src.chains.hospital_cypher_chain import hospital_cypher_chain

question = """Quel est hopital qui a fait objet du plus grand nombre de critiques au cours de année écoulée ?"""

response = hospital_cypher_chain.invoke(question)
result = response.get("result")  
print(result)
