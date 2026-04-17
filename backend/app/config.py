from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = BASE_DIR / "backend"
DATA_DIR = BACKEND_DIR / "data"
STATIC_DIR = BACKEND_DIR / "static"
IMAGES_DIR = STATIC_DIR / "images"
DOCX_CACHE_DIR = DATA_DIR / "docx_cache"
SOURCE_DOC_DIR = BASE_DIR / "预案"
DATABASE_PATH = DATA_DIR / "plans.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"


def ensure_directories() -> None:
    for path in (DATA_DIR, STATIC_DIR, IMAGES_DIR, DOCX_CACHE_DIR):
        path.mkdir(parents=True, exist_ok=True)