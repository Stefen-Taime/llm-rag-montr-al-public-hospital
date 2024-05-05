import sys
sys.path.append('/home/stefen/mtl-H')
import dotenv
dotenv.load_dotenv()
from chatbot_api.src.agents.hospital_rag_agent import hospital_rag_agent_executor

question = {
    "input": "Which hospital has the shortest wait time?"
}

try:
    response = hospital_rag_agent_executor.invoke(question)
    result = response.get("result")
    print(result)
except Exception as e:
    print(f"An error occurred: {e}")

