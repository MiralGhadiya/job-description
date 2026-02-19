import streamlit as st
import requests

# ==============================
# 🔗 API Configuration
# ==============================

API_BASE = "https://glenna-peptonic-unsmoulderingly.ngrok-free.dev"

CLASSIFY_URL = f"{API_BASE}/classify"
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
# 🎨 Styling
# ==============================

st.markdown("""
<style>
.block-container {
    max-width: 900px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}
section[data-testid="stSidebar"] {
    background-color: #0f172a;
}
.custom-card {
    background-color: #111827;
    padding: 1.5rem;
    border-radius: 12px;
    border: 1px solid #1f2937;
    margin-bottom: 1.2rem;
}
.custom-alert {
    background-color: #2d2f14;
    padding: 1rem 1.2rem;
    border-radius: 10px;
    border: 1px solid #3f4220;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ==============================
# 🔧 Session State Defaults
# ==============================

defaults = {
    "session_id": None,
    "resume_mode": "auto",
    "selected_resume": "Auto Select (Semantic Search)",
    "uploaded_resume_file": None,
    "resume_mismatch": None,
    "pending_requirement": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ==============================
# 📥 Backend Fetching
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

# ==============================
# 📄 Resume Options
# ==============================

resume_list = fetch_resumes()
resume_options = ["Auto Select (Semantic Search)"] + resume_list

# ==============================
# ⚙️ Sidebar
# ==============================

with st.sidebar:

    st.title("🤖 Upwork Proposal Bot")

    st.subheader("📄 Resume Options")

    selected_resume = st.selectbox(
        "Select Stored Resume",
        options=resume_options,
        index=resume_options.index(st.session_state.selected_resume)
        if st.session_state.selected_resume in resume_options else 0
    )

    st.session_state.selected_resume = selected_resume

    if selected_resume == "Auto Select (Semantic Search)":
        st.session_state.resume_mode = "auto"
        st.caption("🔍 Backend will auto-select best resume")
    else:
        st.session_state.resume_mode = "stored"
        st.caption(f"✓ Using stored resume: {selected_resume}")

    st.subheader("📤 Upload Resume")

    uploaded_file = st.file_uploader("Upload PDF or TXT Resume", type=["pdf", "txt"])

    if uploaded_file:
        st.session_state.resume_mode = "upload"
        st.session_state.uploaded_resume_file = uploaded_file
        st.success("Uploaded resume will be used.")

    if st.session_state.resume_mode == "upload":
        if st.button("❌ Clear Uploaded Resume"):
            st.session_state.uploaded_resume_file = None
            st.session_state.resume_mode = "auto"
            st.rerun()

    st.markdown("---")

    if st.button("➕ New Application", use_container_width=True):
        for key in ["session_id", "resume_mismatch", "pending_requirement"]:
            st.session_state[key] = None
        st.rerun()

    st.markdown("---")
    st.subheader("💬 Previous Applications")

    sessions = fetch_sessions()

    if sessions:
        for session in sessions:
            if st.button(
                session.get("title", "Untitled")[:40],
                key=f"session_{session['id']}",
                use_container_width=True
            ):
                st.session_state.session_id = session["id"]
                st.session_state.resume_mismatch = None
                st.session_state.pending_requirement = None
                st.rerun()
    else:
        st.caption("No previous chats yet.")

# ==============================
# 💬 Chat Area
# ==============================

if not st.session_state.session_id:
    st.markdown("""
    <div class="custom-card">
        <h2>📝 Start a New Application</h2>
        <p style="color: #9ca3af;">
        Paste a job description below to generate a tailored proposal.
        </p>
    </div>
    """, unsafe_allow_html=True)
else:
    session_data = fetch_single_session(st.session_state.session_id)
    if session_data:
        for msg in session_data.get("conversation", []):
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])


# ==============================
# 🟨 Resume Mismatch UI
# ==============================
if st.session_state.resume_mismatch and st.session_state.pending_requirement:

    mm = st.session_state.resume_mismatch
    best = mm.get("best_match_resume")
    score = mm.get("similarity_score", 0)

    st.markdown(f"""
    <div class="custom-alert">
        <b>Resume Mismatch Detected</b><br/>
        The selected resume does not strongly match this requirement.
    </div>
    <p><b>Best Match:</b> {best}</p>
    <p><b>Similarity Score:</b> {score * 100:.1f}%</p>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Proceed with Best Match", use_container_width=True):

            req = st.session_state.pending_requirement

            st.session_state.resume_mismatch = None
            st.session_state.pending_requirement = None
            st.session_state.resume_mode = "stored"
            st.session_state.selected_resume = best

            r = requests.post(
                GENERATE_URL,
                json={"requirement": req, "resume_name": best},
                timeout=120
            )

            if r.status_code == 200:
                data = r.json()
                if "session_id" in data:
                    st.session_state.session_id = data["session_id"]
                    fetch_sessions.clear()
                    st.rerun()
                else:
                    st.error("Backend did not return session_id.")
            else:
                st.error(r.text)

    with col2:
        if st.button("Cancel", use_container_width=True):
            st.session_state.resume_mismatch = None
            st.session_state.pending_requirement = None
            st.rerun()


# ==============================
# 📝 Chat Input
# ==============================

st.divider()
user_input = st.chat_input("Paste job description or ask follow-up...")

if user_input:

    # Show user message instantly
    with st.chat_message("user"):
        st.markdown(user_input)

    # ==========================
    # FOLLOWUP FLOW
    # ==========================
    if st.session_state.session_id:

        with st.spinner("Thinking..."):
            r = requests.post(
                FOLLOWUP_URL,
                json={
                    "session_id": st.session_state.session_id,
                    "question": user_input
                }
            )

        if r.status_code == 200:
            data = r.json()
            content = data.get("answer") or data.get("proposal")

            if content:
                with st.chat_message("assistant"):
                    st.markdown(content)
            else:
                st.error("Empty response from backend.")

        else:
            st.error(r.text)

    # ==========================
    # NEW PROPOSAL FLOW
    # ==========================
    else:

        classify_response = requests.post(
            CLASSIFY_URL,
            json={"requirement": user_input}
        )

        if classify_response.status_code == 200:
            is_job = classify_response.json().get("is_job_related", False)

            if not is_job:
                with st.chat_message("assistant"):
                    st.markdown(
                        "I am a job-application assistant and can only assist with job-related queries such as proposals, requirements, resume details, or hiring discussions."
                    )
                st.stop()

        with st.spinner("Generating proposal..."):

            try:

                if st.session_state.resume_mode == "upload":
                    uploaded_file = st.session_state.uploaded_resume_file
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file,
                            uploaded_file.type
                        )
                    }

                    r = requests.post(
                        GENERATE_UPLOAD_URL,
                        data={"requirement": user_input},
                        files=files,
                        timeout=120
                    )

                elif st.session_state.resume_mode == "stored":
                    payload = {
                        "requirement": user_input,
                        "resume_name": st.session_state.selected_resume
                    }
                    r = requests.post(GENERATE_URL, json=payload)

                else:
                    r = requests.post(
                        GENERATE_URL,
                        json={"requirement": user_input}
                    )

                if r.status_code == 200:
                    data = r.json()

                    if "best_match_resume" in data and "similarity_score" in data:
                        # store mismatch info + the job text the user pasted
                        st.session_state.resume_mismatch = data
                        st.session_state.pending_requirement = user_input
                        st.rerun()

                    if "error" in data:
                        with st.chat_message("assistant"):
                            st.markdown(data["error"])
                        st.stop()

                    st.session_state.session_id = data["session_id"]
                    fetch_sessions.clear()
                    st.rerun()

                else:
                    st.error(r.text)

            except Exception as e:
                st.error(str(e))
