from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"

embedding_model = SentenceTransformer(EMBED_MODEL)
