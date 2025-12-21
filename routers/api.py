from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import json
from rag.service import rag_service

router = APIRouter(prefix="/coach", tags=["coach"])

class GameContext(BaseModel):
    my_champion: str = Field(..., description="내 챔피언")
    enemy_champion: str = Field(..., description="상대 챔피언")
    game_time: str = Field(..., description="게임 시간")
    current_status: str = Field(..., description="상황")
    user_question: Optional[str] = Field(None, description="질문")

class CoachCard(BaseModel):
    type: str = Field(..., description="카드의 성격")
    title: str = Field(..., description="제목")
    coach_saying: str = Field(..., description="코치 멘트")
    wiki_evidence: str = Field(..., description="근거 데이터")
    # [추가] 출처 필드
    source: str = Field(..., description="정보의 출처 (예: 나무위키-다리우스)") 
    solution: str = Field(..., description="행동 지침")

class AnalysisResponse(BaseModel):
    cards: List[CoachCard]

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_play(context: GameContext):
    try:
        json_str_response = rag_service.provide_feedback(context)
        
        # JSON 파싱 시도
        try:
            # LLM이 줄바꿈 문자 등을 포함할 수 있어 정리 후 파싱
            clean_json = json_str_response.replace("```json", "").replace("```", "").strip()
            card_data_list = json.loads(clean_json)
        except json.JSONDecodeError:
            print(f"❌ JSON 파싱 실패: {json_str_response}")
            # 파싱 실패 시 기본 에러 카드 반환 (앱이 죽지 않도록)
            return {"cards": [{
                "type": "🔧 시스템",
                "title": "코치 연결 불안정",
                "coach_saying": "잠시 통신 상태가 좋지 않아 정밀 분석에 실패했습니다.",
                "wiki_evidence": "서버 응답 오류",
                "solution": "🔄 다시 시도해주세요."
            }]}

        return {"cards": card_data_list}
        
    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))