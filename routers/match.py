from fastapi import APIRouter, HTTPException
from services.riot_service import get_recent_matches

router = APIRouter()

@router.get("/api/matches/{puuid}")
async def get_matches(puuid: str):
    matches = get_recent_matches(puuid)
    
    if not matches:
        # 게임 기록이 없거나 에러인 경우
        return {"status": "error", "matches": []}
        
    return {"status": "success", "matches": matches}