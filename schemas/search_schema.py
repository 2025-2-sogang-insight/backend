from pydantic import BaseModel

class SummonerSearchRequest(BaseModel):
    summoner_name: str
    
class SummonerSearchResponse(BaseModel):
    status: str
    puuid: str # 유저 고유 ID
    game_name: str # 닉네임
    tag_line: str # 태그 (#KR1)
    message: str | None = None