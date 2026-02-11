from app.vectorstore import FaissProjectStore
from app.review_store import FaissReviewStore

excel_path = "evenmore own portfolio.xlsx"

project_store = FaissProjectStore()
project_store.build_from_excel(excel_path)

review_store = FaissReviewStore()
review_store.build_from_excel(excel_path)

print("✅ Project + Review FAISS indexes created")