import faiss
import numpy as np
import pickle
from pathlib import Path
from app.embeddings import embedding_model

DATA_DIR = Path("data")
RESUME_DIR = Path("resume")
INDEX_PATH = DATA_DIR / "resumes.faiss"
META_PATH = DATA_DIR / "resumes_meta.pkl"


class FaissResumeStore:
    def __init__(self):
        self.model = embedding_model
        self.index = None
        self.texts = []
        self.metadata = []

    # -------- BUILD FROM FOLDER --------
    def build_from_folder(self):
        import pdfplumber

        resumes = []

        for file in RESUME_DIR.glob("*"):
            if file.suffix.lower() == ".txt":
                text = file.read_text(encoding="utf-8")

            elif file.suffix.lower() == ".pdf":
                with pdfplumber.open(file) as pdf:
                    text = "\n".join(
                        page.extract_text() or "" for page in pdf.pages
                    )

            else:
                continue

            if not text.strip():
                continue

            resumes.append({
                "name": file.stem,
                "text": text
            })

        if not resumes:
            raise RuntimeError("No valid resumes found in resume/ folder")

        self._build(resumes)

    # -------- INTERNAL BUILD --------
    def _build(self, resumes: list):
        for r in resumes:
            self.texts.append(r["text"])
            self.metadata.append({"name": r["name"]})

        embeddings = self.model.encode(
            self.texts,
            normalize_embeddings=True,
        ).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        DATA_DIR.mkdir(exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))

        with open(META_PATH, "wb") as f:
            pickle.dump((self.texts, self.metadata), f)

        print(f"Built resume index for {len(resumes)} resumes.")

    # -------- LOAD OR AUTO BUILD --------
    def load(self):
        if not INDEX_PATH.exists():
            print("Resume index not found. Building automatically...")
            self.build_from_folder()

        self.index = faiss.read_index(str(INDEX_PATH))

        with open(META_PATH, "rb") as f:
            self.texts, self.metadata = pickle.load(f)

    # -------- SEARCH --------
    def search(self, query: str, top_k: int = 1):
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(query_emb, top_k)

        idx = indices[0][0]

        return {
            "text": self.texts[idx],
            "metadata": self.metadata[idx],
        }
