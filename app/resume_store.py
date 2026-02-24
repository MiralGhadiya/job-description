import faiss
import numpy as np
import pickle
from pathlib import Path
from app.embeddings import embedding_model

DATA_DIR = Path("data")
INDEX_PATH = DATA_DIR / "resumes.faiss"
META_PATH = DATA_DIR / "resumes_meta.pkl"


class FaissResumeStore:
    def __init__(self):
        self.model = embedding_model
        self.index = None
        self.texts = []
        self.metadata = []

    # ---------------- GET BY NAME ----------------
    def get_by_name(self, name: str):
        for text, meta in zip(self.texts, self.metadata):
            if meta["name"].lower() == name.lower():
                return {
                    "text": text,
                    "metadata": meta,
                }
        return None

    # ---------------- LOAD ----------------
    def load(self):
        if not INDEX_PATH.exists() or not META_PATH.exists():
            print("Resume index not found. Creating empty store.")
            DATA_DIR.mkdir(exist_ok=True)
            self.index = None
            self.texts = []
            self.metadata = []
            return

        self.index = faiss.read_index(str(INDEX_PATH))

        with open(META_PATH, "rb") as f:
            self.texts, self.metadata = pickle.load(f)

    # ---------------- SAVE ----------------
    def save(self):
        DATA_DIR.mkdir(exist_ok=True)

        if self.index is not None:
            faiss.write_index(self.index, str(INDEX_PATH))

        with open(META_PATH, "wb") as f:
            pickle.dump((self.texts, self.metadata), f)

    # ---------------- SEARCH ----------------
    def search(self, query: str, top_k: int = 1):
        if self.index is None:
            return None

        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(query_emb, top_k)

        idx = indices[0][0]
        score = float(scores[0][0])

        return {
            "text": self.texts[idx],
            "metadata": self.metadata[idx],
            "score": score
        }

    # ---------------- ADD RESUME ----------------
    def add_resume(self, name: str, text: str):

        # Prevent duplicate names
        for meta in self.metadata:
            if meta["name"].lower() == name.lower():
                raise ValueError("Resume with this name already exists.")

        embedding = self.model.encode(
            [text],
            normalize_embeddings=True
        ).astype("float32")

        if self.index is None:
            dim = embedding.shape[1]
            self.index = faiss.IndexFlatIP(dim)

        self.index.add(embedding)

        self.texts.append(text)
        self.metadata.append({"name": name})

    # ---------------- DELETE RESUME ----------------
    def delete_resume(self, name: str):

        new_texts = []
        new_metadata = []

        for text, meta in zip(self.texts, self.metadata):
            if meta["name"].lower() != name.lower():
                new_texts.append(text)
                new_metadata.append(meta)

        if len(new_texts) == len(self.texts):
            return False

        self.texts = new_texts
        self.metadata = new_metadata

        if not self.texts:
            self.index = None
            return True

        embeddings = self.model.encode(
            self.texts,
            normalize_embeddings=True
        ).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        return True
