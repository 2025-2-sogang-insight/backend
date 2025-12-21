import os
import requests
from urllib.parse import quote
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("RIOT_API_KEY")

HEADERS = {
    "X-Riot-Token": API_KEY
}

REGION_TO_ROUTING = {
    "KR": "asia", "JP": "asia",
    "NA": "americas", "OCE": "americas",
    "EUW": "europe", "EUNE": "europe", "ME1": "europe",
}

REGION_TO_PLATFORM = {
    "KR": "kr", "JP": "jp1",
    "NA": "na1", "OCE": "oc1",
    "EUW": "euw1", "EUNE": "eun1", "ME1": "me1",
}

def get_summoner_info(region_code: str, game_name: str, tag_line: str):
    if not region_code: return None
    region_code = region_code.upper()
    routing = REGION_TO_ROUTING.get(region_code)
    platform = REGION_TO_PLATFORM.get(region_code)
    
    if not routing or not platform:
        print(f"[Error] 지원하지 않는 지역 코드: {region_code}")
        return None

    clean_tag_line = tag_line.replace("#", "")
    safe_game_name = quote(game_name)
    safe_tag_line = quote(clean_tag_line)

    url = f"https://{routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{safe_game_name}/{safe_tag_line}"
    
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200: return None
        account_data = resp.json()
        puuid = account_data['puuid']
        
        # Summoner V4
        sum_url = f"https://{platform}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        resp_sum = requests.get(sum_url, headers=HEADERS)
        if resp_sum.status_code != 200: return None
        summoner_data = resp_sum.json()

        return {
            "puuid": puuid,
            "game_name": account_data['gameName'],
            "tag_line": account_data['tagLine'],
            "profile_icon_id": summoner_data['profileIconId'],
            "region": region_code 
        }
    except Exception as e:
        print(f"[Error] API 호출 예외: {e}")
        return None

def get_recent_matches(puuid: str, region_code: str, count: int = 5):
    region_code = region_code.upper()
    routing = REGION_TO_ROUTING.get(region_code)
    if not routing: return []

    url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids?start=0&count={count}"
    try:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200: return []
        match_ids = resp.json()
    except:
        return []

    match_details = []
    for match_id in match_ids:
        prefix = match_id.split("_")[0].upper()
        if prefix in ["KR", "JP"]: m_routing = "asia"
        elif prefix in ["NA1", "BR1", "LA1", "OC1"]: m_routing = "americas"
        elif prefix in ["EUW1", "EUN1", "TR1", "ME1"]: m_routing = "europe"
        else: m_routing = routing

        m_url = f"https://{m_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        try:
            m_resp = requests.get(m_url, headers=HEADERS)
            if m_resp.status_code != 200: continue
            data = m_resp.json()
            info = data['info']
            part = next((p for p in info['participants'] if p['puuid'] == puuid), None)
            if part:
                match_details.append({
                    "match_id": match_id,
                    "champion_name": part['championName'],
                    "kills": part['kills'],
                    "deaths": part['deaths'],
                    "assists": part['assists'],
                    "win": part['win'],
                    "game_mode": info['gameMode'],
                    "game_creation": info['gameCreation']
                })
        except: continue
    return match_details

def get_match_detail(match_id: str):
    """
    매치 ID로 게임 정보(Info)와 타임라인(Timeline)을 모두 가져옵니다.
    """
    prefix = match_id.split("_")[0].upper()
    if prefix in ["KR", "JP"]: routing = "asia"
    elif prefix in ["NA1", "BR1", "LA1", "OC1"]: routing = "americas"
    elif prefix in ["EUW1", "EUN1", "TR1", "ME1"]: routing = "europe"
    else: routing = "asia"

    base_url = f"https://{routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"

    try:
        info_resp = requests.get(base_url, headers=HEADERS)
        timeline_resp = requests.get(f"{base_url}/timeline", headers=HEADERS)

        if info_resp.status_code != 200 or timeline_resp.status_code != 200:
            print(f"[Error] 매치 데이터 조회 실패: {match_id}")
            return None

        return {
            "match_id": match_id,
            "info": info_resp.json(),
            "timeline": timeline_resp.json()
        }
    except Exception as e:
        print(f"[Error] get_match_detail 예외: {e}")
        return None