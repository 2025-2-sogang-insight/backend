from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import sys
import os

# 서비스 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from services.riot_service import get_recent_matches, get_match_detail

router = APIRouter(prefix="/match", tags=["2. Match"])

# --- 응답 모델 ---
class MatchPreview(BaseModel):
    match_id: str
    champion_name: str
    win: bool
    game_creation: int

class FullGameContext(BaseModel):
    match_data: Dict[str, Any]
    timeline_data: Dict[str, Any]
    target_puuid: Optional[str] = None

# --- API ---

@router.get("/list/{puuid}", response_model=List[MatchPreview])
async def get_match_list(puuid: str, region: str = "KR", count: int = 5):
    """
    [2-1단계] PUUID로 최근 5게임의 매치 ID를 조회합니다.
    """
    matches = get_recent_matches(puuid, region, count)
    return matches

@router.get("/detail/{match_id}", response_model=FullGameContext)
async def get_match_raw_data(match_id: str, puuid: Optional[str] = Query(None)):
    """
    [2-2단계] 매치 ID로 게임 데이터를 가져옵니다.
    ★ 이 결과(JSON) 전체를 복사해서 /coach/analyze 에 넣으세요.
    """
    result = get_match_detail(match_id)
    if not result:
        raise HTTPException(status_code=404, detail="매치 정보를 찾을 수 없습니다.")
    
    return {
        "match_data": result['info'],
        "timeline_data": result['timeline'],
        "target_puuid": puuid # 입력했다면 포함, 안했으면 null
    }