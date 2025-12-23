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
├── main.py                 # FastAPI 앱 엔트리포인트 
├── cv/                     # 컴퓨터 비전 (YOLOv8 & OCR)
│   ├── process_video.py    # 인게임 녹화 영상 분석
│   ├── match_champion.py   # 챔피언 인식 및 추적
│   └── best.pt             # 학습된 YOLO 모델 가중치 
├── routers/                # API 라우터 (기능별 분리)
│   ├── coach.py            # AI 코칭/분석 API
│   ├── match.py            # 매치 히스토리 조회
│   └── search.py           # 소환사 검색
├── rag/                    # RAG (검색 증강 생성) 서비스
│   ├── service.py          # LangChain + LLM 분석 로직
│   ├── settings.py         # 모델 파라미터 및 DB 설정
│   └── create_db.py        # Vector DB 구축 스크립트
├── services/               # 외부 연동
│   └── riot_service.py     # Riot Games API 통신 핸들러
├── schemas/                # 데이터 검증 (Pydantic)
└── uploads/                # 업로드된 리플레이/영상 저장소
```
  
</details>


</details>

<br>

## 🚀 핵심 기능 및 흐름 (Key Features & Flow)</h2></summary>

### <mark>🔄 서비스 유기적 흐름 (Workflow)</mark>

<details>
<summary><strong>Step </strong></summary>
  
**Step 1: 소환사 식별 (Search)**
> 소환사이름과 태그라인을 입력해 고유값(PUUID) 찾음

**Step 2: 데이터 확보 (Match)**
> PUUID로 최근 전적을 조회 & 분석하고 싶은 경기의 상세 데이터를 가져옴

**Step 3: 심층 분석 (Coach)**
> 경기 데이터를 AI에게 전달하면, 승패 요인과 맞춤형 피드백이 담긴 리포트가 생성됨

</details>



<br/>

### <mark>🔍 1. 소환사 검색 (Search)</mark>

<details>
<summary><strong>API 엔드포인트 </strong></summary>
  
`POST /api/search`

</details>

<details>
<summary><strong>기능</strong></summary>
  
- **검색**: 소환사명과 태그라인으로 계정 고유 ID(PUUID) 조회

</details>

<br/>

### <mark>⚔️ 2. 매치 상세 조회 (Match)</mark>

<details>
<summary><strong>API 엔드포인트 </strong></summary>
  
- **목록 조회**: `GET /match/list/{puuid}`
- **상세 조회**: `GET /match/detail/{match_id}`

</details>

<details>
<summary><strong>기능</strong></summary>
  
- **전적 리스트**: 지정한 소환사의 최근 랭크 게임 목록 불러옴
- **데이터 확보**: 특정 경기의 모든 로그(스킬 사용, 아이템 구매, 이동 경로 등) 수집

</details>



<br/>

### <mark>🤖 3. AI 게임 코칭 (Coach)</mark>

<details>
<summary><strong>API 엔드포인트 </strong></summary>
  
`POST /coach/analyze`

</details>

<details>
<summary><strong>기능</strong></summary>
  
- **종합**: 게임 내 발생한 모든 사건과 타임라인 데이터를 하나로 합침
- **분석**: AI가 데이터를 읽고 성과 및 개선점 찾아냄

</details>

<details>
<summary><strong>분석 프로세스 </strong></summary>
  
**① 핵심 요약**: 킬, 데스, 딜량 등 가장 중요한 지표 우선 탐색<br>
**② 승부처 발견**: 게임의 승패가 갈린 결정적인 순간(한타, 오브젝트 싸움) 발견<br>
**③ AI 판단**: 상황 데이터를 바탕으로 "왜 이겼는지" 혹은 "왜 졌는지"를 AI가 판단<br>
**④ 피드백**: 다음 게임에서 활용할 수 있는 구체적인 조언 제공

</details>


<br>

## 🛠 기술 스택 (Tech Stack)</h2></summary>

### <mark>📃 스택 목록</mark>

<details>
<summary><strong>Framework & Language </strong></summary>

- **Python**: 데이터 분석 및 AI 활용 최적화
- **FastAPI**: 비동기 API 서버 및 문서화

</details>

<details>
<summary><strong>AI & Vision </strong></summary>

- **Gemini Pro**: 코칭 리포트 생성을 위한 LLM
- **LangChain**: AI 로직 및 프롬프트 관리
- **YOLOv8**: 챔피언/타워 객체 인식
- **OpenCV**: 영상 데이터 전처리

</details>

<details>
<summary><strong>Data & API </strong></summary>

- **ChromaDB**: 벡터 DB 및 유사도 검색
- **Riot API**: 공식 게임 데이터 제공

</details>



</details>
