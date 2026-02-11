import streamlit as st
import requests

API_URL = "https://glenna-peptonic-unsmoulderingly.ngrok-free.dev/generate/upwork"

st.set_page_config(page_title="Upwork Proposal Bot", layout="centered")

st.title("🤖 Upwork Proposal Generator")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
user_input = st.chat_input("Paste the job description here...")

if user_input:
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    # Call FastAPI
    with st.spinner("Generating proposal..."):
        response = requests.post(
            API_URL,
            json={"requirement": user_input},
        )

        if response.status_code == 200:
            proposal = response.text    
        else:
            proposal = "❌ Error generating proposal."

    # Show bot message
    st.session_state.messages.append({"role": "assistant", "content": proposal})

    with st.chat_message("assistant"):
        st.markdown(proposal)

        st.code(proposal, language="text")
