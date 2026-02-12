import streamlit as st
import requests

API_BASE = "https://interstreet-elza-icy.ngrok-free.dev"
GENERATE_URL = f"{API_BASE}/generate/upwork"
RESUME_URL = f"{API_BASE}/resumes"

st.set_page_config(page_title="Upwork Proposal Bot", layout="centered")

st.title("🤖 Upwork Proposal Generator")

# --------------------------------------------------
# Fetch Resume List (Cached)
# --------------------------------------------------
@st.cache_data(ttl=60)
def fetch_resumes():
    response = requests.get(RESUME_URL, timeout=10)
    response.raise_for_status()
    return response.json().get("resumes", [])

resume_list = fetch_resumes()


# Add Auto option
resume_options = ["Auto Select (Semantic Search)"] + resume_list

# --------------------------------------------------
# Persist Resume Selection Across Reruns
# --------------------------------------------------
if "selected_resume" not in st.session_state:
    st.session_state.selected_resume = "Auto Select (Semantic Search)"

# If resume list changes and stored resume no longer exists
if st.session_state.selected_resume not in resume_options:
    st.session_state.selected_resume = "Auto Select (Semantic Search)"

# --------------------------------------------------
# Sidebar Settings
# --------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")

    selected_resume = st.selectbox(
        "Select Resume",
        options=resume_options,
        index=resume_options.index(st.session_state.selected_resume)
    )

    st.markdown("---")

    if selected_resume == "Auto Select (Semantic Search)":
        st.info("System will automatically choose the most relevant resume.")
    else:
        st.success(f"Using resume: {selected_resume}")

# Save updated selection
st.session_state.selected_resume = selected_resume

st.divider()

# --------------------------------------------------
# Chat History State
# --------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --------------------------------------------------
# Chat Input
# --------------------------------------------------
user_input = st.chat_input("Paste the job description here...")

if user_input:
    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate Proposal
    with st.spinner("Generating proposal..."):

        payload = {
            "requirement": user_input
        }

        # Add resume only if manually selected
        if selected_resume != "Auto Select (Semantic Search)":
            payload["resume_name"] = selected_resume

        try:
            response = requests.post(
                GENERATE_URL,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                proposal = response.text
            else:
                proposal = f"❌ Error: {response.status_code}"

        except Exception:
            proposal = "❌ Unable to connect to backend."

    # Store assistant message
    st.session_state.messages.append({
        "role": "assistant",
        "content": proposal
    })

    with st.chat_message("assistant"):
        st.markdown(proposal)
        st.code(proposal, language="text")
