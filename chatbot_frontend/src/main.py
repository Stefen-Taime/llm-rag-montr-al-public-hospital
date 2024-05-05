import os
import requests
import streamlit as st

CHATBOT_URL = os.getenv("CHATBOT_URL", "http://localhost:8000/hospital-rag-agent")

with st.sidebar:
    st.header("A propos de")
    st.markdown(
        """
        Ce chatbot s'interface avec un
        [LangChain](https://github.com/Stefen-Taime/llm-rag-mtl-public-hospital/blob/main/README.md)
        agent conçu pour répondre aux questions sur les hôpitaux, les patients,
        les visites, Ce projet développe un modèle de type Retrieve-Augment-Generate (RAG) pour répondre aux questions en utilisant les données publiques des avis laissés sur Google pour des hôpitaux à Montréal. Les hôpitaux ciblés incluent l'Hôpital du Sacré-Cœur-de-Montréal, l'Hôpital Maisonneuve-Rosemont, l'Hôpital Jean-Talon, l'Hôpital Notre-Dame - Siège social du CCSMTL, et le CHU Sainte-Justine..
        """
    )

    st.header("Exemples de questions")
    st.markdown("- Quels sont les hôpitaux ayant le plus grand écart entre le nombre de revues positives et négatives")
    st.markdown("- Comparaisons de la satisfaction des patients entre les hôpitaux ?")
    st.markdown(
        "- Quels sont les hôpitaux avec le nombre moyen de revues par visite le plus élevé ?"
    )
    st.markdown("- Que disent les patients de l'efficacité des hôpitaux ? Mentionnez les détails de certaines critiques.")
    

st.title("Hôpital System Chatbot")
st.info(
    "Posez-moi des questions sur les patients, les visites, les hôpitaux, les critiques !"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if "output" in message.keys():
            st.markdown(message["output"])

        if "explanation" in message.keys():
            with st.status("Comment cela a-t-il été généré ?", state="complete"):
                st.info(message["explanation"])

if prompt := st.chat_input("Que voulez-vous savoir ?"):
    st.chat_message("user").markdown(prompt)

    st.session_state.messages.append({"role": "user", "output": prompt})

    data = {"text": prompt}

    with st.spinner("A la recherche d'une réponse..."):
        response = requests.post(CHATBOT_URL, json=data)

        if response.status_code == 200:
            output_text = response.json()["output"]
            explanation = response.json()["intermediate_steps"]

        else:
            output_text = """Une erreur s'est produite lors du traitement de votre message.
            Veuillez réessayer ou reformuler votre message."""
            explanation = output_text

    st.chat_message("assistant").markdown(output_text)
    st.status("Comment cela a-t-il été généré ?", state="complete").info(explanation)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "output": output_text,
            "explanation": explanation,
        }
    )