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
UPLOAD_RESUME_URL = f"{API_BASE}/resumes/upload"

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
# 🔧 Session Defaults
# ==============================

defaults = {
    "session_id": None,
    "resume_mode": "auto",
    "selected_resume": "Auto Select (Semantic Search)",
    "uploaded_resume_file": None,
    "resume_mismatch": None,
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
# ⚙️ Sidebar
# ==============================

with st.sidebar:

    st.title("🤖 Upwork Proposal Bot")

    st.subheader("📄 Resume Options")

    resume_list = fetch_resumes()
    resume_options = ["Auto Select (Semantic Search)"] + resume_list

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

        if st.button("🗑 Delete Selected Resume", use_container_width=True):
            r = requests.delete(f"{API_BASE}/resumes/{selected_resume}")
            if r.status_code == 200:
                st.success("Resume deleted.")
                fetch_resumes.clear()
                st.session_state.selected_resume = "Auto Select (Semantic Search)"
                st.rerun()
            else:
                st.error(r.text)

    st.markdown("---")
    st.subheader("📤 Upload Resume (One-Time Use)")

    uploaded_file = st.file_uploader(
        "Upload PDF or TXT Resume",
        type=["pdf", "txt"],
        key="one_time_upload"
    )

    if uploaded_file:
        st.session_state.resume_mode = "upload"
        st.session_state.uploaded_resume_file = uploaded_file
        st.success("Uploaded resume will be used for next proposal.")

    if st.session_state.resume_mode == "upload":
        if st.button("❌ Clear Uploaded Resume", use_container_width=True):
            st.session_state.uploaded_resume_file = None
            st.session_state.resume_mode = "auto"
            st.rerun()

    st.markdown("---")
    st.subheader("➕ Add Resume To Store")

    new_resume_file = st.file_uploader(
        "Upload Resume (Saved Permanently)",
        type=["pdf", "txt"],
        key="store_upload"
    )

    if st.button("Save Resume To Store", use_container_width=True):

        if new_resume_file:
            resume_name = new_resume_file.name.rsplit(".", 1)[0]

            files = {
                "file": (
                    new_resume_file.name,
                    new_resume_file,
                    new_resume_file.type
                )
            }

            r = requests.post(
                UPLOAD_RESUME_URL,
                data={"resume_name": resume_name},
                files=files
            )

            if r.status_code == 200:
                st.success(f"Resume saved as: {resume_name}")
                fetch_resumes.clear()
                st.rerun()
            else:
                st.error(r.text)
        else:
            st.warning("Please upload a file first.")
            
            
    st.markdown("---")
    st.subheader("📊 Sync Reviews + Projects from Google Sheets")

    reviews_url = st.text_input("Reviews CSV URL (optional)")
    projects_url = st.text_input("Projects CSV URL (required)")

    if st.button("Sync"):
        if not projects_url:
            st.warning("Please enter Projects CSV URL.")
        else:
            # Sync projects (required)
            r_projects = requests.post(
                f"{API_BASE}/sync/google-sheet/projects",
                json={"sheet_url": projects_url}
            )

            # Sync reviews (optional)
            r_reviews = None
            if reviews_url:
                r_reviews = requests.post(
                    f"{API_BASE}/sync/google-sheet/reviews",
                    json={"sheet_url": reviews_url}
                )

            ok_projects = (r_projects.status_code == 200)
            ok_reviews = (r_reviews is None or r_reviews.status_code == 200)

            if ok_projects and ok_reviews:
                st.success("✅ Sync completed successfully.")
            else:
                st.error(
                    f"Projects sync: {r_projects.text}\n"
                    f"Reviews sync: {r_reviews.text if r_reviews else 'SKIPPED'}"
                )
        

    st.markdown("---")
    if st.button("➕ New Application", use_container_width=True):
        st.session_state.session_id = None
        st.session_state.resume_mismatch = None
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
# 🚨 Resume Mismatch UI
# ==============================

if st.session_state.resume_mismatch:

    mismatch = st.session_state.resume_mismatch

    st.markdown("""
    <div class="custom-alert">
        <h4>Resume Mismatch Detected</h4>
        <p>The selected resume does not strongly match this requirement.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write(f"**Best Match:** {mismatch['best_match']}")
    st.write(f"**Similarity Score:** {mismatch['score'] * 100:.1f}%")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ Proceed with Best Match"):
            payload = {
                "requirement": mismatch["requirement"],
                "resume_name": mismatch["best_match"]
            }

            r = requests.post(GENERATE_URL, json=payload)

            if r.status_code == 200:
                data = r.json()
                st.session_state.resume_mismatch = None
                st.session_state.session_id = data["session_id"]
                fetch_sessions.clear()
                st.rerun()

    with col2:
        if st.button("Cancel"):
            st.session_state.resume_mismatch = None
            st.rerun()

    st.stop()

# ==============================
# 📝 Chat Input
# ==============================

st.divider()
user_input = st.chat_input("Paste job description or ask follow-up...")

if user_input:

    with st.chat_message("user"):
        st.markdown(user_input)

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

                    if "best_match_resume" in data:
                        st.session_state.resume_mismatch = {
                            "message": data["error"],
                            "best_match": data["best_match_resume"],
                            "score": data["similarity_score"],
                            "requirement": user_input
                        }
                        st.rerun()

                    st.session_state.session_id = data["session_id"]
                    fetch_sessions.clear()
                    st.rerun()

                else:
                    st.error(r.text)

            except Exception as e:
                st.error(str(e))