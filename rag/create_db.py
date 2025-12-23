import json
import os
import shutil
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from tqdm import tqdm

# [수정] JSON_DIR_OPGG 추가 임포트
from .settings import JSON_DIR, JSON_DIR_OPGG, DB_PATH, EMBEDDING_MODEL

def clean_source_name(filename_stem):
    """
    파일명 정제: "preprocessed_세트(리그-오브-레전드)" -> "세트"
    """
    name = filename_stem.replace("preprocessed_", "")
    name = name.replace("(리그-오브-레전드)", "")
    return name.strip()

def create_vector_db():
    # 1. 처리할 데이터 폴더 목록 정의
    # 나무위키 데이터 경로와 OP.GG 데이터 경로를 리스트로 관리
    source_dirs = [
        {"path": JSON_DIR, "category": "namuwiki"},
        {"path": JSON_DIR_OPGG, "category": "opgg"}
    ]
    
    all_files = []
    
    print("📂 데이터 폴더를 확인합니다...")
    for source in source_dirs:
        dir_path = source["path"]
        category = source["category"]
        
        if os.path.exists(dir_path):
            files = list(dir_path.glob("*.json"))
            print(f"   - [{category}] {len(files)}개의 파일을 발견했습니다. ({dir_path})")
            # 파일 경로와 카테고리를 함께 저장
            for f in files:
                all_files.append({"file_path": f, "category": category})
        else:
            print(f"   ⚠️ [{category}] 폴더가 없습니다: {dir_path}")

    if not all_files:
        print("❌ 처리할 JSON 파일이 하나도 없습니다.")
        return

    # 2. 기존 DB 삭제 (모델 변경/데이터 갱신 시 필수)
    if os.path.exists(DB_PATH):
        print(f"🗑️ 기존 DB 폴더를 삭제하고 새로 만듭니다: {DB_PATH}")
        shutil.rmtree(DB_PATH)
    
    documents = []
    print(f"🚀 총 {len(all_files)}개의 파일을 처리합니다...")

    # 3. 파일 로드 및 문서 생성
    for item in tqdm(all_files):
        file_path = item["file_path"]
        category = item["category"]
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                clean_name = clean_source_name(file_path.stem)
                
                # 데이터 구조 처리
                # Case A: "sections" 키가 있는 경우 (나무위키 구조 등)
                if "sections" in data:
                    for section in data["sections"]:
                        heading = section.get("heading", "")
                        text = section.get("text", "")
                        
                        if not text.strip(): continue
                        
                        # 내용 구성: [카테고리:챔피언명] 소제목 + 내용
                        content = f"[{category.upper()} | {clean_name}] {heading}\n{text}"
                        metadata = {
                            "source": clean_name,
                            "category": category, # namuwiki 또는 opgg
                            "heading": heading,
                            "filename": file_path.name
                        }
                        documents.append(Document(page_content=content, metadata=metadata))
                
                # Case B: "sections"가 없고 바로 데이터가 있는 경우 (OP.GG 단순 데이터 등)
                # 만약 OP.GG 데이터 구조가 다르다면 이 부분을 커스텀해야 합니다.
                # 여기서는 텍스트로 변환 가능한 경우 전체를 하나의 문서로 봅니다.
                else:
                    text_content = json.dumps(data, ensure_ascii=False, indent=2)
                    content = f"[{category.upper()} | {clean_name}] 전체 데이터\n{text_content}"
                    metadata = {
                        "source": clean_name,
                        "category": category,
                        "heading": "Full Data",
                        "filename": file_path.name
                    }
                    documents.append(Document(page_content=content, metadata=metadata))

        except Exception as e:
            print(f"⚠️ 파일 로드 실패 ({file_path.name}): {e}")

    if not documents:
        print("❌ 생성된 문서(Documents)가 없습니다.")
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
    print(f"   - 총 처리 파일: {len(all_files)}개")
    print(f"   - 총 청크 수: {len(splits)}개")
    print("-" * 50)

if __name__ == "__main__":
    create_vector_db()