import faiss
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from app.embeddings import embedding_model
from sentence_transformers import SentenceTransformer


DATA_DIR = Path("data")
INDEX_PATH = DATA_DIR / "projects.faiss"
META_PATH = DATA_DIR / "projects_meta.pkl"

EMBED_MODEL = "all-MiniLM-L6-v2"

PROJECT_SHEETS = {
    "PHP PROJECT LIST": "PHP Project",
    "FLUTTER PROJECT LIST": "Flutter Project",
    "PYTHON PROJECT LIST": "Python Project",
}

class FaissProjectStore:
    def __init__(self):
        self.model = embedding_model
        self.index = None
        self.texts = []
        self.metadata = []

    def build_from_excel(self, excel_path: str):
        xls = pd.ExcelFile(excel_path)

        for sheet, category in PROJECT_SHEETS.items():
            df = xls.parse(sheet)

            for _, row in df.iterrows():
                text = self._row_to_text(row, category)
                if not text.strip():
                    continue

                self.texts.append(text)
                self.metadata.append({
                    "project_name": str(row.get("PROJECT NAME", "")).strip(),
                    "category": category,
                    "industry": str(row.get("INDUSTRY", "")).strip(),
                })

        embeddings = self.model.encode(
            self.texts,
            show_progress_bar=True,
            normalize_embeddings=True,
        )

        embeddings = np.array(embeddings).astype("float32")

        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)  # cosine similarity
        self.index.add(embeddings)

        DATA_DIR.mkdir(exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))

        with open(META_PATH, "wb") as f:
            pickle.dump((self.texts, self.metadata), f)

    def load(self):
        self.index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            self.texts, self.metadata = pickle.load(f)

    def search(self, query: str, top_k: int = 3) -> str:
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(query_emb, top_k)
        results = [self.texts[i] for i in indices[0]]

        return "\n\n".join(results)
    
    def search_debug(self, query: str, top_k: int = 5):
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(query_emb, top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            results.append({
                "score": float(score),
                "text": self.texts[idx],
                "metadata": self.metadata[idx],
            })

        return results


    def _row_to_text(self, row, category: str) -> str:
        return f"""
            Project: {row.get('PROJECT NAME', '')}
            Project Type: {row.get('Unnamed: 1', '')}
            Category: {category}
            Industry: {row.get('INDUSTRY', '')}
            Tech Stack: {row.get('Tech Stack', '')}
            Description: {row.get('DESCRIPTION', '')}
            """.strip()
