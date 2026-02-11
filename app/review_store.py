import faiss
import pandas as pd
import numpy as np
import pickle
from pathlib import Path
from sentence_transformers import SentenceTransformer

DATA_DIR = Path("data")
INDEX_PATH = DATA_DIR / "reviews.faiss"
META_PATH = DATA_DIR / "reviews_meta.pkl"

EMBED_MODEL = "all-MiniLM-L6-v2"

class FaissReviewStore:
    def __init__(self):
        self.model = SentenceTransformer(EMBED_MODEL)
        self.index = None
        self.texts = []
        self.metadata = []

    def build_from_excel(self, excel_path: str):
        xls = pd.ExcelFile(excel_path)
        df = xls.parse("Rating Review")

        for _, row in df.iterrows():
            text = self._row_to_text(row)
            if not text.strip():
                continue

            self.texts.append(text)
            self.metadata.append({
                "product": str(row.get("Product Name", "")).strip(),
                "rating": row.get("Rating"),
                "country": str(row.get("Country", "")).strip(),
            })

        embeddings = self.model.encode(
            self.texts,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        embeddings = np.array(embeddings).astype("float32")
        dim = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)

        DATA_DIR.mkdir(exist_ok=True)
        faiss.write_index(self.index, str(INDEX_PATH))

        with open(META_PATH, "wb") as f:
            pickle.dump((self.texts, self.metadata), f)

    def load(self):
        self.index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "rb") as f:
            self.texts, self.metadata = pickle.load(f)

    def search(self, query: str, top_k: int = 2) -> str:
        query_emb = self.model.encode(
            [query],
            normalize_embeddings=True,
        ).astype("float32")

        scores, indices = self.index.search(query_emb, top_k)
        return "\n".join(self.texts[i] for i in indices[0])

    def _row_to_text(self, row) -> str:
        return f"""
        Review for: {row.get('Product Name', '')}
        Rating: {row.get('Rating')} stars
        Client Location: {row.get('Country', '')}
        Feedback: {row.get('Review / Comment', '')}
        """.strip()
