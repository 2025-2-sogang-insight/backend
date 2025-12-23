import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 프로젝트 루트 경로 (2차인콘)
BASE_DIR = Path(__file__).resolve().parents[2]

# 데이터 경로 설정 (프로젝트 루트의 data 폴더)
DATA_DIR = BASE_DIR / "data"

# [중요] JSON 파일이 있는 실제 경로 (나무위키 데이터)
JSON_DIR = DATA_DIR / "preprocessed" / "namuwiki" / "outputs" / "per-article"

JSON_DIR_OPGG = DATA_DIR / "preprocessed" / "opgg" / "outputs"

# 벡터 DB 저장 경로
DB_PATH = DATA_DIR / "chroma_db"

# [모델 설정]
EMBEDDING_MODEL = "text-embedding-3-small"

# LLM: Google Gemini (빠름/무료 티어)
LLM_MODEL = "gemini-2.5-flash"