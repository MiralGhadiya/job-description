import streamlit as st
import requests
from datetime import datetime

# ==============================
# 🔗 API Configuration
# ==============================

API_BASE = "https://interstreet-elza-icy.ngrok-free.dev"

GENERATE_URL = f"{API_BASE}/generate/upwork"
GENERATE_UPLOAD_URL = f"{API_BASE}/generate/upwork/upload"
FOLLOWUP_URL = f"{API_BASE}/generate/upwork/followup"
RESUME_URL = f"{API_BASE}/resumes"
SESSIONS_URL = f"{API_BASE}/sessions"

st.set_page_config(
    page_title="Upwork Proposal Bot",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================
# 📥 Fetch Backend Data
# ==============================

@st.cache_data(ttl=60)
def fetch_resumes():
    try:
        r = requests.get(RESUME_URL, timeout=10)
        r.raise_for_status()
        return r.json().get("resumes", [])
    except:
        return []

@st.cache_data(ttl=30)
def fetch_sessions():
    try:
        r = requests.get(SESSIONS_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except:
        return []

def fetch_single_session(session_id):
    try:
        r = requests.get(f"{API_BASE}/sessions/{session_id}", timeout=10)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


resume_list = fetch_resumes()
resume_options = ["Auto Select (Semantic Search)"] + resume_list

# ==============================
# 🧠 Session State
# ==============================

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "selected_resume" not in st.session_state:
    st.session_state.selected_resume = "Auto Select (Semantic Search)"

if st.session_state.selected_resume not in resume_options:
    st.session_state.selected_resume = "Auto Select (Semantic Search)"

# ==============================
# ⚙️ Sidebar
# ==============================

with st.sidebar:

    st.title("🤖 Upwork Proposal Bot")
    st.markdown("---")

    # Resume Selection
    st.subheader("📄 Resume Options")

    selected_resume = st.selectbox(
        "Select Stored Resume",
        options=resume_options,
        index=resume_options.index(st.session_state.selected_resume)
    )

    st.session_state.selected_resume = selected_resume

    if selected_resume == "Auto Select (Semantic Search)":
        st.caption("🔍 Backend will auto-select best resume")
    else:
        st.caption(f"✓ Using stored resume: {selected_resume}")

    st.markdown("---")

    # Upload Resume
    st.subheader("📤 Upload New Resume (Optional)")
    uploaded_file = st.file_uploader(
        "Upload PDF or TXT Resume",
        type=["pdf", "txt"]
    )

    if uploaded_file:
        st.success(f"Ready to use uploaded file: {uploaded_file.name}")

    st.markdown("---")

    # New Chat Button
    if st.button("➕ New Application", use_container_width=True):
        st.session_state.session_id = None
        st.rerun()

    st.markdown("---")

    # Chat History
    st.subheader("💬 Previous Applications")

    sessions = fetch_sessions()

    if sessions:
        for session in sessions:
            if st.button(
                session["title"][:50] + "...",
                key=session["id"],
                use_container_width=True
            ):
                st.session_state.session_id = session["id"]
                st.rerun()
    else:
        st.info("No previous chats yet.")

# ==============================
# 💬 Main Chat Area
# ==============================

if st.session_state.session_id:
    session_data = fetch_single_session(st.session_state.session_id)

    if session_data:
        conversation = session_data.get("conversation", [])

        for msg in conversation:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    else:
        st.error("Could not load session.")

else:
    st.markdown("## 📝 Start a New Application")
    st.markdown("Paste a job description below to generate a proposal.")

# ==============================
# 📝 Chat Input
# ==============================

user_input = st.chat_input("Paste job description or ask follow-up...")

if user_input:

    # ----------------------------
    # FOLLOW-UP MODE
    # ----------------------------
    if st.session_state.session_id:

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    r = requests.post(
                        FOLLOWUP_URL,
                        json={
                            "session_id": st.session_state.session_id,
                            "question": user_input
                        },
                        timeout=60
                    )

                    if r.status_code == 200:
                        answer = r.json().get("answer", "")
                        st.markdown(answer)
                    else:
                        st.error("Error in follow-up.")

                except Exception as e:
                    st.error(str(e))

        st.rerun()

    # ----------------------------
    # INITIAL GENERATION MODE
    # ----------------------------
    else:

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Generating proposal..."):

                try:

                    # 🔥 CASE 1: Upload Resume
                    if uploaded_file:

                        files = {
                            "file": (
                                uploaded_file.name,
                                uploaded_file,
                                uploaded_file.type
                            )
                        }

                        data = {
                            "requirement": user_input
                        }

                        r = requests.post(
                            GENERATE_UPLOAD_URL,
                            data=data,
                            files=files,
                            timeout=120
                        )

                    # 🔥 CASE 2: Stored Resume
                    else:

                        payload = {
                            "requirement": user_input
                        }

                        if selected_resume != "Auto Select (Semantic Search)":
                            payload["resume_name"] = selected_resume

                        r = requests.post(
                            GENERATE_URL,
                            json=payload,
                            timeout=120
                        )

                    # ----------------------------
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state.session_id = data["session_id"]
                        st.markdown(data["proposal"])
                    else:
                        st.error(f"Error: {r.status_code}")
                        st.code(r.text)

                except Exception as e:
                    st.error(str(e))

        st.rerun()
