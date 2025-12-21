from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import sys
import os

# 서비스 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

try:
    from rag.service import rag_service
except ImportError:
    from backend.rag.service import rag_service

router = APIRouter(prefix="/coach", tags=["3. Coach"])

# --- 모델 ---
class FullGameContext(BaseModel):
    match_data: Dict[str, Any] = Field(..., description="매치 데이터")
    timeline_data: Dict[str, Any] = Field(..., description="타임라인 데이터")
    target_puuid: Optional[str] = Field(None, description="분석 대상 PUUID")

class AnalysisResponse(BaseModel):
    one_line_review: str
    match_flow: Any
    skirmish_analysis: Any
    play_eval: Any
    team_atmosphere: Any

# --- API ---
@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_game(context: FullGameContext):
    """
    [3단계] 복사한 매치 데이터를 붙여넣으면 AI 분석 결과를 반환합니다.
    (target_puuid가 꼭 있어야 합니다!)
    """
    if not context.target_puuid:
        raise HTTPException(status_code=400, detail="target_puuid가 비어있습니다. JSON에 값을 채워주세요.")

    try:
        result = rag_service.generate_report(
            match_data=context.match_data,
            timeline_data=context.timeline_data,
            target_puuid=context.target_puuid
        )
        return result
    except Exception as e:
        print(f"Analysis Error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))