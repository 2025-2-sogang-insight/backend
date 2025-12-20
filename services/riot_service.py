import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")

HEADERS = {
    "X-Riot-Token": API_KEY
}

def get_summoner_info(full_name: str):
    # 1. 입력값 파싱
    if "#" in full_name:
        game_name, tag_line = full_name.split("#")
    else:
        game_name = full_name
        tag_line = "KR1"

    print(f"[Riot Service] {game_name} #{tag_line} 검색 시작...")

    # [수정된 부분] 닉네임에 한글/띄어쓰기가 있어도 안전하게 변환 (URL Encoding)
    safe_game_name = quote(game_name)
    safe_tag_line = quote(tag_line)

    # --- Step 1: Account-V1 ---
    # 주소에 변환된 이름(safe_game_name)을 넣습니다.
    account_url = f"https://asia.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{safe_game_name}/{safe_tag_line}"
    
    resp = requests.get(account_url, headers=HEADERS)
    
    if resp.status_code != 200:
        print(f"[Error] Account API 실패: {resp.status_code} - {resp.text}")
        return None
    
    account_data = resp.json()
    puuid = account_data['puuid']
    
    # 닉네임이 바뀌었을 수도 있으니, API가 준 최신 이름으로 업데이트
    real_game_name = account_data['gameName']
    real_tag_line = account_data['tagLine']

    # --- Step 2: Summoner-V4 ---
    summoner_url = f"https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    
    resp_sum = requests.get(summoner_url, headers=HEADERS)
    
    if resp_sum.status_code != 200:
        print(f"[Error] Summoner API 실패: {resp_sum.status_code}")
        return None

    summoner_data = resp_sum.json()

    return {
        "puuid": puuid,
        "game_name": real_game_name,
        "tag_line": real_tag_line,
        "level": summoner_data['summonerLevel'],
        "profile_icon_id": summoner_data['profileIconId']
    }
    
def get_recent_matches(puuid: str, count: int=5):
    print(f"[Riot Service] PUUID로 최근 {count}게임 조회 시작...")
    
    # 1. 매치 ID 리스트 가져오기 (Asia 서버)
    match_ids_url = f"https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    resp = requests.get(match_ids_url, headers=HEADERS)
    
    if resp.status_code != 200:
        return []
    
    match_ids = resp.json()
    match_details = []
    
    # 2. 각 매치 상세 정보 가져오기
    for match_id in match_ids:
        url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}"
        m_resp = requests.get(url, headers=HEADERS)
        
        if m_resp.status_code == 200:
            data = m_resp.json()
            info = data['info']
            
            # "나(검색한 사람)"의 정보만 찾기
            participant = next((p for p in info['participants'] if p['puuid'] == puuid), None)
            
            if participant:
                match_details.append({
                    "match_id": match_id,
                    "champion_name": participant['championName'],
                    "kills": participant['kills'],
                    "deaths": participant['deaths'],
                    "assists": participant['assists'],
                    "win": participant['win'],  # True/False
                    "game_mode": info['gameMode'] # ARAM, CLASSIC 등
                })
    
    return match_details