import streamlit as st
import requests

# ==============================
# 🔗 API Configuration
# ==============================

API_BASE = "https://interstreet-elza-icy.ngrok-free.dev"
GENERATE_URL = f"{API_BASE}/generate/upwork"
FOLLOWUP_URL = f"{API_BASE}/generate/upwork/followup"
RESUME_URL = f"{API_BASE}/resumes"

st.set_page_config(page_title="Upwork Proposal Bot", layout="centered")

st.title("🤖 Upwork Proposal Generator")

# ==============================
# 📥 Fetch Available Resumes
# ==============================

@st.cache_data(ttl=60)
def fetch_resumes():
    response = requests.get(RESUME_URL, timeout=10)
    response.raise_for_status()
    return response.json().get("resumes", [])

resume_list = fetch_resumes()
resume_options = ["Auto Select (Semantic Search)"] + resume_list

# ==============================
# 🧠 Session State Setup
# ==============================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "selected_resume" not in st.session_state:
    st.session_state.selected_resume = "Auto Select (Semantic Search)"

if st.session_state.selected_resume not in resume_options:
    st.session_state.selected_resume = "Auto Select (Semantic Search)"

# ==============================
# ⚙️ Sidebar Settings
# ==============================

with st.sidebar:
    st.header("⚙️ Settings")

    selected_resume = st.selectbox(
        "Select Resume",
        options=resume_options,
        index=resume_options.index(st.session_state.selected_resume)
    )

    st.session_state.selected_resume = selected_resume

    st.markdown("---")

    if selected_resume == "Auto Select (Semantic Search)":
        st.info("System will automatically choose the most relevant resume.")
    else:
        st.success(f"Using resume: {selected_resume}")

    st.markdown("---")

    if st.button("🔄 New Application"):
        st.session_state.session_id = None
        st.session_state.messages = []
        st.rerun()

st.divider()

# ==============================
# 💬 Display Chat History
# ==============================

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==============================
# 📝 User Input
# ==============================

user_input = st.chat_input("Paste the job description or ask follow-up...")

if user_input:

    # Display user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # ===================================
    # 🔥 FOLLOW-UP MODE
    # ===================================
    if st.session_state.session_id:

        with st.spinner("Generating answer..."):
            try:
                response = requests.post(
                    FOLLOWUP_URL,
                    json={
                        "session_id": st.session_state.session_id,
                        "question": user_input
                    },
                    timeout=60
                )

                if response.status_code == 200:
                    answer = response.json()["answer"]
                else:
                    answer = f"❌ Error: {response.status_code}"

            except Exception:
                answer = "❌ Unable to connect to backend."

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer
        })

        with st.chat_message("assistant"):
            st.markdown(answer)

    # ===================================
    # 🚀 INITIAL PROPOSAL MODE
    # ===================================
    else:

        with st.spinner("Generating proposal..."):

            payload = {
                "requirement": user_input
            }

            if selected_resume != "Auto Select (Semantic Search)":
                payload["resume_name"] = selected_resume

            try:
                response = requests.post(
                    GENERATE_URL,
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    data = response.json()
                    proposal = data["proposal"]
                    st.session_state.session_id = data["session_id"]
                else:
                    proposal = f"❌ Error: {response.status_code}"

            except Exception:
                proposal = "❌ Unable to connect to backend."

        st.session_state.messages.append({
            "role": "assistant",
            "content": proposal
        })

        with st.chat_message("assistant"):
            st.markdown(proposal)
