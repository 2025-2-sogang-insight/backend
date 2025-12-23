import requests

def print_teams_by_side(api_key, match_id):
    # 한국/아시아 서버 기준 URL
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}"
    resp = requests.get(url, headers={"X-Riot-Token": api_key}).json()
    
    participants = resp['info']['participants']
    
    blue_team = [] # Team ID 100
    red_team = []  # Team ID 200
    
    for p in participants:
        champ = p['championName']
        if p['teamId'] == 100:
            blue_team.append(champ)
        else:
            red_team.append(champ)

    print(f"=== 매치 ID: {match_id} ===")
    print(f"🟦 블루팀: {', '.join(blue_team)}")
    print(f"🟥 레드팀: {', '.join(red_team)}")
    return [blue_team, red_team]

API_KEY = os.getenv("RIOT_API_KEY") # .env에 RIOT_API_KEY 설정 필요
MATCH_ID = "KR_7971051219" # 테스트할 매치 ID

champions = print_teams_by_side(API_KEY, MATCH_ID)

# 1. 챔피언 DB (내용은 동일)
CHAMPION_DB = [
  { "name": "Aatrox", "kr_name": "아트록스", "role": "Frontline Bruiser" },
  { "name": "Ahri", "kr_name": "아리", "role": "Assassin & Diver" },
  { "name": "Akali", "kr_name": "아칼리", "role": "Assassin & Diver" },
  { "name": "Akshan", "kr_name": "아크샨", "role": "Assassin & Diver" },
  { "name": "Alistar", "kr_name": "알리스타", "role": "Initiator" },
  { "name": "Amumu", "kr_name": "아무무", "role": "Initiator" },
  { "name": "Anivia", "kr_name": "애니비아", "role": "Variable & Poke" },
  { "name": "Annie", "kr_name": "애니", "role": "Initiator" },
  { "name": "Aphelios", "kr_name": "아펠리오스", "role": "Main Dealer" },
  { "name": "Ashe", "kr_name": "애쉬", "role": "Main Dealer" },
  { "name": "Aurelion Sol", "kr_name": "아우렐리온 솔", "role": "Main Dealer" },
  { "name": "Aurora", "kr_name": "오로라", "role": "Assassin & Diver" },
  { "name": "Azir", "kr_name": "아지르", "role": "Main Dealer" },
  { "name": "Bard", "kr_name": "바드", "role": "Variable & Poke" },
  { "name": "Bel'Veth", "kr_name": "벨베스", "role": "Main Dealer" },
  { "name": "Blitzcrank", "kr_name": "블리츠크랭크", "role": "Variable & Poke" },
  { "name": "Brand", "kr_name": "브랜드", "role": "Main Dealer" },
  { "name": "Braum", "kr_name": "브라움", "role": "Utility & Protect" },
  { "name": "Briar", "kr_name": "브라이어", "role": "Assassin & Diver" },
  { "name": "Caitlyn", "kr_name": "케이틀린", "role": "Main Dealer" },
  { "name": "Camille", "kr_name": "카밀", "role": "Assassin & Diver" },
  { "name": "Cassiopeia", "kr_name": "카시오페아", "role": "Main Dealer" },
  { "name": "Cho'Gath", "kr_name": "초가스", "role": "Frontline Bruiser" },
  { "name": "Corki", "kr_name": "코르키", "role": "Main Dealer" },
  { "name": "Darius", "kr_name": "다리우스", "role": "Frontline Bruiser" },
  { "name": "Diana", "kr_name": "다이애나", "role": "Initiator" },
  { "name": "Dr. Mundo", "kr_name": "문도 박사", "role": "Frontline Bruiser" },
  { "name": "Draven", "kr_name": "드레이븐", "role": "Main Dealer" },
  { "name": "Ekko", "kr_name": "에코", "role": "Assassin & Diver" },
  { "name": "Elise", "kr_name": "엘리스", "role": "Assassin & Diver" },
  { "name": "Evelynn", "kr_name": "이블린", "role": "Assassin & Diver" },
  { "name": "Ezreal", "kr_name": "이즈리얼", "role": "Main Dealer" },
  { "name": "Fiddlesticks", "kr_name": "피들스틱", "role": "Initiator" },
  { "name": "Fiora", "kr_name": "피오라", "role": "Assassin & Diver" },
  { "name": "Fizz", "kr_name": "피즈", "role": "Assassin & Diver" },
  { "name": "Galio", "kr_name": "갈리오", "role": "Initiator" },
  { "name": "Gangplank", "kr_name": "갱플랭크", "role": "Main Dealer" },
  { "name": "Garen", "kr_name": "가렌", "role": "Frontline Bruiser" },
  { "name": "Gnar", "kr_name": "나르", "role": "Initiator" },
  { "name": "Gragas", "kr_name": "그라가스", "role": "Initiator" },
  { "name": "Graves", "kr_name": "그레이브즈", "role": "Main Dealer" },
  { "name": "Gwen", "kr_name": "그웬", "role": "Frontline Bruiser" },
  { "name": "Hecarim", "kr_name": "헤카림", "role": "Initiator" },
  { "name": "Heimerdinger", "kr_name": "하이머딩거", "role": "Variable & Poke" },
  { "name": "Hwei", "kr_name": "흐웨이", "role": "Variable & Poke" },
  { "name": "Illaoi", "kr_name": "일라오이", "role": "Frontline Bruiser" },
  { "name": "Irelia", "kr_name": "이렐리아", "role": "Assassin & Diver" },
  { "name": "Ivern", "kr_name": "아이번", "role": "Utility & Protect" },
  { "name": "Janna", "kr_name": "잔나", "role": "Utility & Protect" },
  { "name": "Jarvan IV", "kr_name": "자르반 4세", "role": "Initiator" },
  { "name": "Jax", "kr_name": "잭스", "role": "Assassin & Diver" },
  { "name": "Jayce", "kr_name": "제이스", "role": "Variable & Poke" },
  { "name": "Jhin", "kr_name": "진", "role": "Main Dealer" },
  { "name": "Jinx", "kr_name": "징크스", "role": "Main Dealer" },
  { "name": "K'Sante", "kr_name": "크산테", "role": "Frontline Bruiser" },
  { "name": "Kai'Sa", "kr_name": "카이사", "role": "Main Dealer" },
  { "name": "Kalista", "kr_name": "칼리스타", "role": "Main Dealer" },
  { "name": "Karma", "kr_name": "카르마", "role": "Utility & Protect" },
  { "name": "Karthus", "kr_name": "카서스", "role": "Main Dealer" },
  { "name": "Kassadin", "kr_name": "카사딘", "role": "Assassin & Diver" },
  { "name": "Katarina", "kr_name": "카타리나", "role": "Assassin & Diver" },
  { "name": "Kayle", "kr_name": "케일", "role": "Main Dealer" },
  { "name": "Kayn", "kr_name": "케인", "role": "Assassin & Diver" },
  { "name": "Kennen", "kr_name": "케넨", "role": "Initiator" },
  { "name": "Kha'Zix", "kr_name": "카직스", "role": "Assassin & Diver" },
  { "name": "Kindred", "kr_name": "킨드레드", "role": "Main Dealer" },
  { "name": "Kled", "kr_name": "클레드", "role": "Initiator" },
  { "name": "Kog'Maw", "kr_name": "코그모", "role": "Main Dealer" },
  { "name": "LeBlanc", "kr_name": "르블랑", "role": "Assassin & Diver" },
  { "name": "Lee Sin", "kr_name": "리 신", "role": "Assassin & Diver" },
  { "name": "Leona", "kr_name": "레오나", "role": "Initiator" },
  { "name": "Lillia", "kr_name": "릴리아", "role": "Initiator" },
  { "name": "Lissandra", "kr_name": "리산드라", "role": "Initiator" },
  { "name": "Lucian", "kr_name": "루시안", "role": "Main Dealer" },
  { "name": "Lulu", "kr_name": "룰루", "role": "Utility & Protect" },
  { "name": "Lux", "kr_name": "럭스", "role": "Variable & Poke" },
  { "name": "Malphite", "kr_name": "말파이트", "role": "Initiator" },
  { "name": "Malzahar", "kr_name": "말자하", "role": "Variable & Poke" },
  { "name": "Maokai", "kr_name": "마오카이", "role": "Initiator" },
  { "name": "Master Yi", "kr_name": "마스터 이", "role": "Assassin & Diver" },
  { "name": "Milio", "kr_name": "밀리오", "role": "Utility & Protect" },
  { "name": "Miss Fortune", "kr_name": "미스 포츈", "role": "Main Dealer" },
  { "name": "Mordekaiser", "kr_name": "모데카이저", "role": "Frontline Bruiser" },
  { "name": "Morgana", "kr_name": "모르가나", "role": "Utility & Protect" },
  { "name": "Naafiri", "kr_name": "나피리", "role": "Assassin & Diver" },
  { "name": "Nami", "kr_name": "나미", "role": "Utility & Protect" },
  { "name": "Nasus", "kr_name": "나서스", "role": "Frontline Bruiser" },
  { "name": "Nautilus", "kr_name": "노틸러스", "role": "Initiator" },
  { "name": "Neeko", "kr_name": "니코", "role": "Initiator" },
  { "name": "Nidalee", "kr_name": "니달리", "role": "Variable & Poke" },
  { "name": "Nilah", "kr_name": "닐라", "role": "Main Dealer" },
  { "name": "Nocturne", "kr_name": "녹턴", "role": "Assassin & Diver" },
  { "name": "Nunu & Willump", "kr_name": "누누와 윌럼프", "role": "Initiator" },
  { "name": "Olaf", "kr_name": "올라프", "role": "Frontline Bruiser" },
  { "name": "Orianna", "kr_name": "오리아나", "role": "Initiator" },
  { "name": "Ornn", "kr_name": "오른", "role": "Initiator" },
  { "name": "Pantheon", "kr_name": "판테온", "role": "Assassin & Diver" },
  { "name": "Poppy", "kr_name": "뽀삐", "role": "Utility & Protect" },
  { "name": "Pyke", "kr_name": "파이크", "role": "Assassin & Diver" },
  { "name": "Qiyana", "kr_name": "키아나", "role": "Assassin & Diver" },
  { "name": "Quinn", "kr_name": "퀸", "role": "Assassin & Diver" },
  { "name": "Rakan", "kr_name": "라칸", "role": "Initiator" },
  { "name": "Rammus", "kr_name": "람머스", "role": "Initiator" },
  { "name": "Rek'Sai", "kr_name": "렉사이", "role": "Assassin & Diver" },
  { "name": "Rell", "kr_name": "렐", "role": "Initiator" },
  { "name": "Renata Glasc", "kr_name": "레나타 글라스크", "role": "Utility & Protect" },
  { "name": "Renekton", "kr_name": "레넥톤", "role": "Frontline Bruiser" },
  { "name": "Rengar", "kr_name": "렝가", "role": "Assassin & Diver" },
  { "name": "Riven", "kr_name": "리븐", "role": "Assassin & Diver" },
  { "name": "Rumble", "kr_name": "럼블", "role": "Main Dealer" },
  { "name": "Ryze", "kr_name": "라이즈", "role": "Main Dealer" },
  { "name": "Samira", "kr_name": "사미라", "role": "Main Dealer" },
  { "name": "Sejuani", "kr_name": "세주아니", "role": "Initiator" },
  { "name": "Senna", "kr_name": "세나", "role": "Main Dealer" },
  { "name": "Seraphine", "kr_name": "세라핀", "role": "Utility & Protect" },
  { "name": "Sett", "kr_name": "세트", "role": "Frontline Bruiser" },
  { "name": "Shaco", "kr_name": "샤코", "role": "Assassin & Diver" },
  { "name": "Shen", "kr_name": "쉔", "role": "Utility & Protect" },
  { "name": "Shyvana", "kr_name": "쉬바나", "role": "Frontline Bruiser" },
  { "name": "Singed", "kr_name": "신지드", "role": "Frontline Bruiser" },
  { "name": "Sion", "kr_name": "사이온", "role": "Frontline Bruiser" },
  { "name": "Sivir", "kr_name": "시비르", "role": "Main Dealer" },
  { "name": "Skarner", "kr_name": "스카너", "role": "Initiator" },
  { "name": "Smolder", "kr_name": "스몰더", "role": "Main Dealer" },
  { "name": "Sona", "kr_name": "소나", "role": "Utility & Protect" },
  { "name": "Soraka", "kr_name": "소라카", "role": "Utility & Protect" },
  { "name": "Swain", "kr_name": "스웨인", "role": "Frontline Bruiser" },
  { "name": "Sylas", "kr_name": "사일러스", "role": "Assassin & Diver" },
  { "name": "Syndra", "kr_name": "신드라", "role": "Variable & Poke" },
  { "name": "Tahm Kench", "kr_name": "탐 켄치", "role": "Utility & Protect" },
  { "name": "Taliyah", "kr_name": "탈리야", "role": "Variable & Poke" },
  { "name": "Talon", "kr_name": "탈론", "role": "Assassin & Diver" },
  { "name": "Taric", "kr_name": "타릭", "role": "Utility & Protect" },
  { "name": "Teemo", "kr_name": "티모", "role": "Variable & Poke" },
  { "name": "Thresh", "kr_name": "쓰레쉬", "role": "Variable & Poke" },
  { "name": "Tristana", "kr_name": "트리스타나", "role": "Main Dealer" },
  { "name": "Trundle", "kr_name": "트런들", "role": "Frontline Bruiser" },
  { "name": "Tryndamere", "kr_name": "트린다미어", "role": "Frontline Bruiser" },
  { "name": "Twisted Fate", "kr_name": "트위스티드 페이트", "role": "Variable & Poke" },
  { "name": "Twitch", "kr_name": "트위치", "role": "Main Dealer" },
  { "name": "Udyr", "kr_name": "우디르", "role": "Frontline Bruiser" },
  { "name": "Urgot", "kr_name": "우르곳", "role": "Frontline Bruiser" },
  { "name": "Varus", "kr_name": "바루스", "role": "Main Dealer" },
  { "name": "Vayne", "kr_name": "베인", "role": "Main Dealer" },
  { "name": "Veigar", "kr_name": "베이가", "role": "Variable & Poke" },
  { "name": "Vel'Koz", "kr_name": "벨코즈", "role": "Variable & Poke" },
  { "name": "Vex", "kr_name": "벡스", "role": "Assassin & Diver" },
  { "name": "Vi", "kr_name": "바이", "role": "Initiator" },
  { "name": "Viego", "kr_name": "비에고", "role": "Assassin & Diver" },
  { "name": "Viktor", "kr_name": "빅토르", "role": "Main Dealer" },
  { "name": "Vladimir", "kr_name": "블라디미르", "role": "Main Dealer" },
  { "name": "Volibear", "kr_name": "볼리베어", "role": "Frontline Bruiser" },
  { "name": "Warwick", "kr_name": "워윅", "role": "Assassin & Diver" },
  { "name": "Wukong", "kr_name": "오공", "role": "Initiator" },
  { "name": "Xayah", "kr_name": "자야", "role": "Main Dealer" },
  { "name": "Xerath", "kr_name": "제라스", "role": "Variable & Poke" },
  { "name": "Xin Zhao", "kr_name": "신 짜오", "role": "Assassin & Diver" },
  { "name": "Yasuo", "kr_name": "야스오", "role": "Assassin & Diver" },
  { "name": "Yone", "kr_name": "요네", "role": "Assassin & Diver" },
  { "name": "Yorick", "kr_name": "요릭", "role": "Frontline Bruiser" },
  { "name": "Yuumi", "kr_name": "유미", "role": "Utility & Protect" },
  { "name": "Zac", "kr_name": "자크", "role": "Initiator" },
  { "name": "Zed", "kr_name": "제드", "role": "Assassin & Diver" },
  { "name": "Zeri", "kr_name": "제리", "role": "Main Dealer" },
  { "name": "Ziggs", "kr_name": "직스", "role": "Variable & Poke" },
  { "name": "Zilean", "kr_name": "질리언", "role": "Utility & Protect" },
  { "name": "Zoe", "kr_name": "조이", "role": "Variable & Poke" },
  { "name": "Zyra", "kr_name": "자이라", "role": "Variable & Poke" },
  { "name": "Ambessa", "kr_name": "암베사", "role": "Assassin & Diver" }
]

def normalize_name(name):
    return name.lower().replace(" ", "").replace("'", "").replace(".", "")

# 검색 최적화용 맵 생성 (전체 DB가 있다고 가정)
ROLE_MAP = {normalize_name(c['name']): c['role'] for c in CHAMPION_DB}

def get_match_participants(api_key, match_id):
    """
    API에서 매치 정보를 가져와 참가자들의 상세 정보를 리스트로 반환합니다.
    (단순 이름뿐만 아니라 puuid, teamId, riotId를 포함)
    """
    url = f"https://asia.api.riotgames.com/lol/match/v5/matches/{match_id}"
    try:
        resp = requests.get(url, headers={"X-Riot-Token": api_key})
        resp.raise_for_status() # 에러 체크
        data = resp.json()
    except Exception as e:
        print(f"❌ API 요청 실패: {e}")
        return None

    participants_data = []
    
    info = data.get('info', {})
    participants = info.get('participants', [])

    print(f"=== 매치 ID: {match_id} 데이터 로드 완료 ===")

    for p in participants:
        # 필요한 정보 추출
        p_data = {
            "teamId": p['teamId'], # 100: Blue, 200: Red
            "championName": p['championName'],
            "puuid": p['puuid'],
            "riotIdGameName": p.get('riotIdGameName', ''),
            "riotIdTagLine": p.get('riotIdTagLine', '')
        }
        participants_data.append(p_data)

    return participants_data

def process_match_data(participants_data, target_puuid=None):
    """
    참가자 데이터를 받아 역할(Role)을 매핑하고, 
    target_puuid와 일치하는 플레이어를 식별합니다.
    """
    result = {
        "metadata": {
            "target_puuid": target_puuid
        },
        "analysis_target": None, # 분석 대상 플레이어 정보만 따로 저장
        "blue_team": [],
        "red_team": []
    }

    if not participants_data:
        return result

    for p in participants_data:
        champ_name = p['championName']
        n_name = normalize_name(champ_name)
        role = ROLE_MAP.get(n_name, "Unknown Role") # DB에 없으면 Unknown
        
        # 분석 대상 여부 확인
        is_target = (p['puuid'] == target_puuid)

        # 결과 객체 생성
        player_info = {
            "champion": champ_name,
            "role": role,
            "riot_id": f"{p['riotIdGameName']}#{p['riotIdTagLine']}",
            "is_target": is_target
        }

        # 팀 분류
        if p['teamId'] == 100:
            result["blue_team"].append(player_info)
        else:
            result["red_team"].append(player_info)
        
        # 분석 대상이라면 별도 필드에도 저장 (빠른 접근용)
        if is_target:
            # 타겟 플레이어의 팀 색상 정보 추가
            player_info_copy = player_info.copy()
            player_info_copy["team_color"] = "Blue" if p['teamId'] == 100 else "Red"
            result["analysis_target"] = player_info_copy

    return result

# --- 실행 설정 ---
API_KEY = os.getenv("RIOT_API_KEY") 
MATCH_ID = "KR_7971051219"  # 예시 매치 ID (본인의 매치 ID로 변경 필요)

# ★ 분석하고 싶은 플레이어의 PUUID 입력
# (API로 소환사 정보를 조회해서 얻거나, 이전 매치 데이터에서 복사해오세요)
TARGET_PUUID = "3Tb67761olI0CDbAm9sghuiLQ5Un6t8E5d7Mt3s1EEjivA0WiDJJDRowGPzrC91RwL2E5gb47Yhfuw" 

# 1. 데이터 가져오기 (API 호출)
raw_participants = get_match_participants(API_KEY, MATCH_ID)

# 2. 데이터 가공 및 타겟 식별
if raw_participants:
    final_result = process_match_data(raw_participants, target_puuid=TARGET_PUUID)

    # 3. 결과 출력
    print("\n[분석 결과 요약]")
    target = final_result.get('analysis_target')
    if target:
        print(f"🎯 분석 대상 발견: {target['riot_id']} ({target['team_color']} 팀)")
        print(f"   - 챔피언: {target['champion']}")
        print(f"   - 역할군: {target['role']}")
    else:
        print("⚠️ 해당 매치에서 타겟 플레이어를 찾을 수 없습니다.")

    # 4. JSON 저장
    OUTPUT_FILENAME = "match_analysis.json"
    with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
        json.dump(final_result, f, indent=4, ensure_ascii=False)
    print(f"\n✅ 상세 데이터 저장 완료: {OUTPUT_FILENAME}")

