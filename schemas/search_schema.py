from pydantic import BaseModel

class SummonerSearchRequest(BaseModel):
    game_name: str
    region: str
    tag_line: str
    
class SummonerSearchResponse(BaseModel):
    status: str
    puuid: str # 유저 고유 ID
    game_name: str # 닉네임
    tag_line: str # 태그 (#KR1)
    profile_icon_id: int
    message: str | None = None