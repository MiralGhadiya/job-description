# 🎨 Streamlit Frontend Setup

## Updated for New API Structure

The Streamlit frontend has been updated to work with the new `/api/v1/` API structure.

---

## ⚡ Quick Start

### Terminal 1: Start the Backend
```bash
cd c:\Users\ev\Desktop\job-description
.\venv\Scripts\Activate.ps1
uvicorn app.main_new:app --reload --port 8000
```

The backend will be available at: **http://localhost:8000**

API endpoints will be at: **http://localhost:8000/api/v1/**

### Terminal 2: Start the Frontend
```bash
cd c:\Users\ev\Desktop\job-description\frontend
streamlit run streamlit_app.py
```

The frontend will open at: **http://localhost:8501**

---

## 🔗 API Configuration

**File**: [frontend/streamlit_app.py](./frontend/streamlit_app.py#L11)

```python
API_BASE = "http://localhost:8000/api/v1"
```

### For Production Deployment

When deploying to production, update the `API_BASE` variable to your production domain:

```python
# For development
API_BASE = "http://localhost:8000/api/v1"

# For production
API_BASE = "https://yourdomain.com/api/v1"

# For ngrok tunnel
API_BASE = "https://your-ngrok-url.ngrok-free.dev/api/v1"
```

---

## 📋 Available Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/classify` | POST | Classify if input is job-related |
| `/generate/upwork` | POST | Generate proposal |
| `/generate/upwork/upload` | POST | Generate with uploaded resume |
| `/generate/upwork/followup` | POST | Handle follow-up questions |
| `/resumes` | GET | List all resumes |
| `/resumes` | DELETE | Delete resume |
| `/resumes/upload` | POST | Upload resume |
| `/sessions` | GET | List all sessions |
| `/sessions/{id}` | GET | Get session details |
| `/sync/google-sheet/projects` | POST | Sync projects |
| `/sync/google-sheet/reviews` | POST | Sync reviews |

---

## ✅ Verification Checklist

- [ ] Backend started: `uvicorn app.main_new:app --reload`
- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend started: `streamlit run streamlit_app.py`
- [ ] Frontend accessible at `http://localhost:8501`
- [ ] No connection errors in Streamlit console
- [ ] Can paste job description and get response
- [ ] All features working (resume upload, sync, sessions, etc.)

---

## 🐛 Troubleshooting

### "Failed to connect to backend"
1. Make sure backend is running: `uvicorn app.main_new:app --reload`
2. Check that it's on port 8000
3. Verify API_BASE points to correct URL
4. Check firewall settings

### "Module 'app' not found"
1. Make sure you're in the project root: `cd c:\Users\ev\Desktop\job-description`
2. Activate virtual environment first
3. Run: `uvicorn app.main_new:app --reload`

### "Port 8000 already in use"
```bash
# Kill existing process on port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main_new:app --reload --port 8001
```

### "Port 8501 already in use"
```bash
# Run Streamlit on different port
streamlit run streamlit_app.py --server.port 8502
```

---

## 📁 File Structure

```
job-description/
├── app/                    # Backend (new structure)
│   ├── main_new.py         # FastAPI app factory
│   ├── core/               # Configuration
│   ├── services/           # Business logic
│   ├── api/v1/             # API routes
│   └── utils/              # Utilities
├── frontend/
│   └── streamlit_app.py    # Frontend (updated)
└── venv/                   # Virtual environment
```

---

## 🚀 Deployment Notes

### Local Development
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:8501`
- API Base: `http://localhost:8000/api/v1`

### Staging
- Update `API_BASE` to staging URL
- Test all features before production

### Production
- Update `API_BASE` to production URL
- Use environment variables for security
- Enable proper CORS settings
- Use HTTPS for all connections

---

## 📚 Related Documentation

- [Backend Architecture](./ARCHITECTURE.md) - How backend is structured
- [API Reference](./QUICK_REFERENCE.md) - All endpoints documented
- [Getting Started](./GETTING_STARTED.md) - Full setup guide
- [Refactoring Guide](./REFACTORING_GUIDE.md) - Technical details

---

## ✨ Changes from Old Structure

| Aspect | Before | After |
|--------|--------|-------|
| **Backend** | monolithic main.py | modular app/main_new.py |
| **API Base** | ngrok URL | localhost:8000 |
| **Endpoints** | Direct routes | /api/v1/ prefixed |
| **Configuration** | Scattered | app/core/constants.py |
| **Error Handling** | Generic | Custom exceptions |
| **Logging** | Print statements | Centralized logger |

---

**Next Steps:**
1. Start backend (`uvicorn app.main_new:app --reload`)
2. Start frontend (`streamlit run streamlit_app.py`)
3. Test proposal generation
4. Verify all features work
5. Deploy when ready!

Good luck! 🚀
