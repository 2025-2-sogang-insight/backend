import json
import os
import shutil
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm
from .settings import JSON_DIR, DB_PATH, EMBEDDING_MODEL

def clean_source_name(filename_stem):
    """
    파일명 정제: "preprocessed_세트(리그-오브-레전드)" -> "세트"
    """
    name = filename_stem.replace("preprocessed_", "")
    name = name.replace("(리그-오브-레전드)", "")
    return name.strip()

def create_vector_db():
    # 1. JSON 폴더 확인
    if not os.path.exists(JSON_DIR):
        print(f"❌ 데이터 폴더가 없습니다: {JSON_DIR}")
        return

    documents = []
    files = list(JSON_DIR.glob("*.json"))
    
    if not files:
        print(f"❌ '{JSON_DIR}' 안에 JSON 파일이 없습니다.")
        return

    # 2. 기존 DB 삭제 (모델 변경 시 필수)
    if os.path.exists(DB_PATH):
        print(f"🗑️ 기존 DB 폴더를 삭제하고 새로 만듭니다: {DB_PATH}")
        shutil.rmtree(DB_PATH)
    
    print(f"📂 총 {len(files)}개의 JSON 파일을 처리합니다...")

    # 3. 파일 로드 및 문서 생성
    for file_path in tqdm(files):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                clean_name = clean_source_name(file_path.stem)
                
                if "sections" in data:
                    for section in data["sections"]:
                        heading = section.get("heading", "")
                        text = section.get("text", "")
                        
                        if not text.strip(): continue
                        
                        # 내용 구성: [챔피언명] 소제목 + 내용
                        content = f"[{clean_name}] {heading}\n{text}"
                        metadata = {
                            "source": clean_name,
                            "heading": heading,
                            "filename": file_path.name
                        }
                        documents.append(Document(page_content=content, metadata=metadata))
        except Exception as e:
            print(f"⚠️ 파일 로드 실패 ({file_path.name}): {e}")

    if not documents:
        print("❌ 저장할 데이터가 없습니다.")
        return

    # 4. 텍스트 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    splits = text_splitter.split_documents(documents)
    print(f"✂️ {len(splits)}개의 청크로 분할했습니다.")
    
    # 5. 임베딩 및 DB 저장 (OpenAI)
    print(f"⏳ OpenAI 임베딩({EMBEDDING_MODEL})으로 DB 구축 중...")
    
    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=str(DB_PATH)
    )
    
    print("-" * 50)
    print(f"🎉 DB 구축 완료! 저장 경로: {DB_PATH}")
    print("-" * 50)

if __name__ == "__main__":
    create_vector_db()