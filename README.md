# LOL Coach AI Backend README
<br>

## ⚙️ 개발 환경 설정 (Setup)

### <mark>🎯 필수 요구사항</mark>

**기반 환경**
- **Python 3.9+**: 최신 비동기 처리를 위한 파이썬 버전 필요
- **API Key**: Riot Games API Key 및 Google Gemini 키 발급

<br/>

### <mark>🚀 설치 및 실행 (Installation)</mark>

<details>
<summary><strong>1. 가상환경 및 라이브러리</strong></summary>

- **가상환경 생성**: 프로젝트 격리를 위해 `venv` 생성 및 활성화
- **의존성 설치**: `requirements.txt`에 명시된 필수 라이브러리 일괄 설치
```bash
# 가상환경 세팅
python -m venv venv
venv\Scripts\activate

# 라이브러리 설치
pip install -r requirements.txt
```
</details>

<details>
<summary><strong>2. 환경 변수 설정 (.env)</strong></summary>

- **보안**: API 키는 코드에 노출하지 않고 `.env` 파일로 관리함
- **설정값**: `RIOT_API_KEY`, `GOOGLE_API_KEY` 필수 입력
</details>

<details>
<summary><strong>3. 서버 실행</strong></summary>

- **개발 모드**: 자동 재시작(Hot Reload) 지원 모드로 서버 실행
- **접속 주소**: http://localhost:8000 (Swagger UI: /docs)
```bash
uvicorn main:app --reload
```
</details>
<br>

## 📂 프로젝트 구조 (Structure)</h2></summary>

### <mark>💾 디렉토리 구조</mark>

<details>
  <summary><strong>디렉토리 구조</strong></summary>
  
```
backend/

├── main.py                 # FastAPI 서버 엔트리포인트 
├── routers/                # API 라우터
│   ├── coach.py            # AI 코칭 통합 엔드포인트
│   ├── match.py            # 매치 데이터 조회
│   └── search.py           # 소환사 검색
├── cv/                     # [New] 컴퓨터 비전 & 영상 처리
│   ├── process_video.py    # YOLOv8 영상 분석 및 객체 추적
│   ├── extract_game_time.py# Gemini Vision 활용 게임 시간 동기화
│   ├── report_vision.py    # Vision + API 데이터 기반 코칭 리포트 생성
│   └── best.pt             # Custom 학습된 YOLO 모델 파일
├── rag/                    # RAG (검색 증강 생성) 서비스
│   ├── service.py          # LangChain + LLM 분석 로직
│   ├── settings.py         # 모델 파라미터 및 DB 설정
│   └── create_db.py        # Vector DB 구축 스크립트
├── services/               # 외부 연동
│   └── riot_service.py     # Riot Games API 통신 핸들러
└── schemas/                # 데이터 검증 (Pydantic)
```
  
</details>


</details>

<br>

## 🚀 핵심 기능 및 흐름 (Key Features & Flow)</h2></summary>

### <mark>🔄 서비스 유기적 흐름 (Workflow)</mark>

<details>
<summary><strong>Step </strong></summary>
  
**Step 1: 소환사 식별 (Search)**
> 소환사명으로 고유 식별자(PUUID)를 조회하여 분석 계정을 선택

**Step 2: 데이터 확보 (Match)**
> 해당 소환사의 최근 전적 리스트를 불러와 분석할 경기를 선택

**Step 3: 심층 분석 (Coach)**
> 선택된 경기에 해당하는 API 데이터를 AI에게 전달하여 정밀 코칭 리포트를 생성함

</details>

### 1. 👁️ 멀티모달 AI 분석 (Multi-modal AI Analysis)
![alt text](image.png)
텍스트 데이터(API)와 시각 데이터(Video)를 모두 이용하여 게임에 대한 전반적인 내용과 플레이어의 교전 플레이에 대해 분석합니다.

- **Object Detection (YOLOv8)**: 
  - 인게임 영상에서 챔피언 객체를 탐지합니다.
  - 좌표 데이터를 추출하여 플레이어의 포지셔닝(Positioning) 및 무빙을 픽셀 단위로 분석합니다. (`cv/process_video.py`)

- **Visual Time Sync (Gemini Vision)**:
  - 영상의 타임스탬프와 실제 게임 시간을 동기화하기 위해 Gemini Vision 모델이 게임 화면 내 시간을 OCR을 통해 인식합니다.
  - 이를 통해 영상의 타임라인에 해당하는 Riot API 데이터를 정확하게 매칭합니다. (`cv/extract_game_time.py`)

### 2. 🤖 RAG 기반 정밀 코칭 (RAG Coaching)
- **지식 검색 (RAG)**: ChromaDB에 저장된 프로 선수들의 운영법/공략 데이터를 이용해 사용자의 플레이 데이터를 분석합니다.
- **게임 피드백 제공**: 사용자가 선택한 게임에 해당하는 API 데이터를 이용하여 게임에 대한 다양한 시각의 피드백을 제공합니다.

### 3. 📊 종합 데이터 파이프라인
1. **소환사 검색 & 매치 조회**: 소환사 이름을 이용해 분석을 원하는 매치 선택 및 API 데이터 추출
2. **매치 분석** : 분석 매치에 해당하는 API 데이터를 이용해 LLM이 사용자에게 제공할 수 있는 피드백 구성
3. **대상 영상 분석**: YOLO로 객체 위칫값 추출 & Gemini로 게임 시간 동기화
4. **타임라인 결합**: Vision 데이터와 Riot Match-V5 타임라인 데이터 결합 (`cv/report_vision.py`)후 LLM이 상황을 종합
5. **최종 코칭**: 매치를 분석한 피드백과 영상을 분석한 피드백을 사용자에게 제공

<br/>

| 구분 | 기술 스택 | 설명 |
|------|-----------|------|
| **Framework** | **FastAPI** | 고성능 비동기 Python 웹 프레임워크 |
| **Vision AI** | **YOLOv8** | 실시간 객체 탐지 및 추적 (Tracking) |
| **Generative AI**| **Google Gemini Pro/Flash** | 텍스트 분석 및 Vision(이미지 인식) 처리 |
| **Orchestration**| **LangChain** | LLM 프롬프트 관리 및 체이닝 |
| **Vector DB** | **ChromaDB** | 유사도 검색을 위한 임베딩 저장소 |
| **Data Source** | **Riot Games API** | Match-V5, Summoner-V4 데이터 |
