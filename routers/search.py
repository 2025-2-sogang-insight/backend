from fastapi import APIRouter, HTTPException
from schemas.search_schema import SummonerSearchRequest, SummonerSearchResponse
from services.riot_service import get_summoner_info

router = APIRouter()

@router.post("/api/search", response_model=SummonerSearchResponse)
async def search_summoner(request: SummonerSearchRequest):
    # 서비스 호출
    result = get_summoner_info(request.region, request.game_name, request.tag_line)
    
    if not result:
        raise HTTPException(status_code=404, detail="소환사를 찾을 수 없거나 API 키가 만료되었습니다.")
    
    return SummonerSearchResponse(
        status="success",
        puuid=result["puuid"],
        game_name=result["game_name"],
        tag_line=result["tag_line"],
        profile_icon_id=result["profile_icon_id"],
        message="검색 성공"
    )
    