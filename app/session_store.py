# app/session_store.py
import uuid

class ApplicationSessionStore:
    def __init__(self):
        self.sessions = {}

    def create(self, data: dict) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = data
        return session_id

    def get(self, session_id: str):
        return self.sessions.get(session_id)

    def exists(self, session_id: str) -> bool:
        return session_id in self.sessions