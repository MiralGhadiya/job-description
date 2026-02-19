from app.resume_store import FaissResumeStore
from app.review_store import FaissReviewStore
from app.vectorstore import FaissProjectStore

RESUME_FOLDER = "resume"
EXCEL_FILE = "evenmore own portfolio.xlsx"


def build_all():
    print("\n🚀 Building ALL FAISS indexes...\n")

    # Resume index
    print("📄 Building Resume Index...")
    resume_store = FaissResumeStore()
    resume_store.build_from_folder()
    print("✅ Resume index built.\n")

    # Review index
    print("⭐ Building Review Index...")
    review_store = FaissReviewStore()
    review_store.build_from_excel(EXCEL_FILE)
    print("✅ Review index built.\n")

    # Project index
    print("📦 Building Project Index...")
    project_store = FaissProjectStore()
    project_store.build_from_excel(EXCEL_FILE)
    print("✅ Project index built.\n")

    print("🎉 All indexes built successfully!")


if __name__ == "__main__":
    build_all()
