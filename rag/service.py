import json
import os
import re
import sys
from typing import Dict, List, Any

# [라이브러리 임포트]
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

load_dotenv()

from .settings import DB_PATH, EMBEDDING_MODEL, LLM_MODEL

# =============================================================================
# 1. Data Processor (Riot API 전처리)
# =============================================================================
class RiotMatchDataProcessor:
    def __init__(self, match_data: Dict, timeline_data: Dict):
        self.match = match_data.get('info', {})
        self.timeline = timeline_data.get('info', {})
        self.participants_map = {p['participantId']: p['championName'] for p in self.match.get('participants', [])}

    def get_participant_name(self, p_id):
        return self.participants_map.get(p_id, f"Unknown({p_id})")

    def process_match_summary(self):
        game_overview = {
            "gameDuration": self.match.get('gameDuration'),
            "gameMode": self.match.get('gameMode'),
            "teams": []
        }
        for team in self.match.get('teams', []):
            team_info = {
                "teamId": team['teamId'],
                "win": team['win'],
                "objectives": team.get('objectives', {}),
                "total_kills": team.get('objectives', {}).get('champion', {}).get('kills', 0)
            }
            game_overview['teams'].append(team_info)

        player_stats = []
        for p in self.match.get('participants', []):
            stats = {
                "participantId": p['participantId'],
                "puuid": p.get('puuid'),
                "championName": p['championName'],
                "teamPosition": p.get('teamPosition'),
                "teamId": p['teamId'],
                "items": [p.get(f'item{i}') for i in range(7)],
                "kda": f"{p['kills']}/{p['deaths']}/{p['assists']}",
                "goldEarned": p['goldEarned'],
                "level": p['champLevel'],
                "damageDealt": p['totalDamageDealtToChampions'],
                "damageTaken": p['totalDamageTaken'],
                "visionScore": p['visionScore'],
                "pings": { 
                    "command": p.get('commandPings', 0),
                    "danger": p.get('dangerPings', 0),
                    "getBack": p.get('getBackPings', 0),
                    "enemyMissing": p.get('enemyMissingPings', 0),
                    "assistMe": p.get('assistMePings', 0)
                }
            }
            player_stats.append(stats)
        return {"overview": game_overview, "players": player_stats}

    def process_timeline_summary(self):
        frames_summary = []
        TARGET_EVENTS = {'CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'BUILDING_KILL', 'TURRET_PLATE_DESTROYED'}

        for frame in self.timeline.get('frames', []):
            timestamp = frame['timestamp']
            minute = int(timestamp / 60000)
            
            player_status = {}
            for p_id_str, p_data in frame.get('participantFrames', {}).items():
                p_id = int(p_id_str)
                name = self.get_participant_name(p_id)
                player_status[name] = {
                    "gold": p_data['totalGold'],
                    "level": p_data['level'],
                    "pos": (p_data.get('position', {}).get('x'), p_data.get('position', {}).get('y'))
                }

            events = []
            for event in frame.get('events', []):
                if event['type'] not in TARGET_EVENTS: continue
                
                evt_data = {"type": event['type'], "time": f"{minute}분"}
                if event['type'] == 'CHAMPION_KILL':
                    evt_data.update({
                        "killer": self.get_participant_name(event.get('killerId')),
                        "victim": self.get_participant_name(event.get('victimId')),
                        "assists": [self.get_participant_name(aid) for aid in event.get('assistingParticipantIds', [])],
                        "damage_received": [
                           {"attacker": dmg.get('name'), "spell": dmg.get('spellName')} 
                           for dmg in event.get('victimDamageReceived', [])
                        ]
                    })
                elif event['type'] in ['ELITE_MONSTER_KILL', 'BUILDING_KILL']:
                    evt_data.update({
                        "killer": self.get_participant_name(event.get('killerId')),
                        "object": event.get('monsterType') or event.get('towerType')
                    })
                events.append(evt_data)
            frames_summary.append({"minute": minute, "events": events, "status_snapshot": player_status})
        return frames_summary

    def generate_context(self):
        return {
            "match_summary": self.process_match_summary(),
            "timeline_flow": self.process_timeline_summary()
        }

# =============================================================================
# 2. Match Event Detector (중요 장면 감지)
# =============================================================================
class MatchEventDetector:
    def __init__(self, timeline_flow: List[Dict]):
        self.timeline = timeline_flow

    def detect_key_moments(self) -> List[str]:
        analysis_tasks = []
        for frame in self.timeline:
            minute = frame['minute']
            events = frame['events']
            
            kill_count = sum(1 for e in events if e['type'] == 'CHAMPION_KILL')
            if kill_count >= 3:
                analysis_tasks.append(f"[{minute}분대] 대규모 교전 (총 {kill_count}킬 발생)")
            elif kill_count >= 1 and minute < 15:
                analysis_tasks.append(f"[{minute}분대] 라인전 킬 발생")

            for event in events:
                if event['type'] == 'ELITE_MONSTER_KILL':
                    monster = event.get('object', 'Unknown Monster')
                    analysis_tasks.append(f"[{minute}분대] {monster} 획득 및 교전 확인")

        return list(set(analysis_tasks))
    
import requests

def get_lol_skill_dictionary():
    # 1. 최신 버전 정보 가져오기
    version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    version = requests.get(version_url).json()[0]
    
    print(f"Current LoL Version: {version}")

    # 2. 전체 챔피언 데이터 가져오기 (영어 & 한국어)
    # championFull.json은 모든 스킬 상세 정보를 포함합니다.
    url_en = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"
    url_ko = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/championFull.json"

    data_en = requests.get(url_en).json()["data"]
    data_ko = requests.get(url_ko).json()["data"]

    skill_dict = {}

    # 3. 챔피언별로 순회하며 스킬 매핑
    for champ_id in data_en:
        # 챔피언 정보 (영문/한글)
        champ_en = data_en[champ_id]
        champ_ko = data_ko[champ_id]

        # 패시브 스킬 매핑
        passive_en = champ_en["passive"]["name"]
        passive_ko = champ_ko["passive"]["name"]
        skill_dict[passive_en] = passive_ko

        # Q, W, E, R 스킬 매핑
        # spells 리스트 순서: Q(0), W(1), E(2), R(3)
        for i in range(len(champ_en["spells"])):
            spell_en = champ_en["spells"][i]["name"]
            spell_ko = champ_ko["spells"][i]["name"]
            skill_dict[spell_en] = spell_ko

    return skill_dict

   
full_skill_dict = get_lol_skill_dictionary()

import requests

def get_champion_name_mapping():
    # 1. 최신 버전 확인
    version_url = "https://ddragon.leagueoflegends.com/api/versions.json"
    version = requests.get(version_url).json()[0]
    
    # 2. 영어/한국어 챔피언 데이터 요청 (champion.json은 가벼워서 금방 됩니다)
    url_en = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/champion.json"
    url_ko = f"http://ddragon.leagueoflegends.com/cdn/{version}/data/ko_KR/champion.json"
    
    data_en = requests.get(url_en).json()['data']
    data_ko = requests.get(url_ko).json()['data']
    
    mapping = {}
    
    # 3. 매핑 (ID를 키로 사용하여 이름 매칭)
    for champ_id in data_en:
        en_name = data_en[champ_id]['name']
        ko_name = data_ko[champ_id]['name']
        mapping[en_name] = ko_name
        
    return mapping

full_champion_dict = get_champion_name_mapping()

# =============================================================================
# 3. RAG Service (메인 서비스)
# =============================================================================
class RAGService:
    def __init__(self):
        # 1. 모델 설정
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        
        # Path 객체일 경우 문자열로 변환 (Chroma 호환성)
        db_path_str = str(DB_PATH)
        
        if os.path.exists(db_path_str):
            self.vectorstore = Chroma(persist_directory=db_path_str, embedding_function=self.embeddings)
            self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
            print(f"✅ Vector DB Loaded: {db_path_str}")
        else:
            print(f"⚠️ Vector DB Not Found at {db_path_str}. API Mode Only.")
            self.retriever = None

        self.llm = ChatGoogleGenerativeAI(model=LLM_MODEL, temperature=0.5)

        # 2. 프롬프트 (전체 분석용 하나만 유지)
        self.prompt = ChatPromptTemplate.from_template("""
        # Role
        당신은 League of Legends (LoL) 전문 AI 분석가입니다. 
        사용자가 업로드한 경기 데이터를 바탕으로 심층 분석 리포트를 **JSON 형식**으로 작성합니다.
         

        내용 출력 시 유의점 :                                              
         - 모든 챔피언과 아이템은 한국어로 출력할 것. 영어로 절대 나타내지 않을 것
         - team 100은 블루팀, team 200은 레드팀으로 출력할 것 ('team100', 'team200' 단어는 출력에 나오지 않음)
         - 스킬에 대해 언급할 때에는 {full_skill_dict}을 참고해, 틀리지 않도록 매치하여 그 스킬의 키(Q,W,E,R)와 한국어 번역으로 언급할 것 ( ex : '키'('스킬명"), 챔피언 이름은 붙이지 말기(caitlynq -> Q(필트오버 피스메이커)))
         - 챔피언에 대해 언급할 때에는 {full_champion_dict}을 참고해 꼭 한국어로 이름을 표기하고, 영어 이름은 출력 어디에도 절대 표기하지 말 것.
         - basickattack이 들어가면 "기본 공격" 으로만 번역할것 (ex : caitlynbasicattack ->  기본 공격)
         - 핑 또한 한국어로 번역하여 언급할 것 (예 : 위험핑, 미아핑)
         - API에서 숫자로 존재하는 raw data 내용들을 출력에 절대 포함하지 말 것.
         - Horde는 전령으로 번역할것, BARON_NASHOR는 바론으로 번역할 것
                          


        모든 내용

        # Analysis Target
        - **분석 대상 플레이어**: {target_champion} ({target_position})
        - **상대 라이너/조합**: {enemy_champions}
        - **감지된 중요 장면**: {detected_moments}

        # Data Sources
        1. **Game Logs (API Data)**: {match_context}
        2. **Wiki Knowledge**: {knowledge_context}

        # Report Structure (JSON Output Only)
        아래 목차에 맞춰 분석 내용을 JSON 키(Key)에 매핑하여 작성하십시오. 
        **Markdown 태그(```json 등) 없이 순수 JSON 문자열만 출력해야 합니다.**
                                                       
        # 모든 플레이어의 역할 및 승리/패배 기여로 분류
            분석 가이드라인:

            1. 챔피언 & 포지션 식별: 입력된 챔피언들이 해당 포지션에서 어떤 역할(예: 탱커, 하이퍼 캐리, 유틸폿, 암살자 등)인지 파악하십시오.
            2. 핵심 지표 가중치 평가: 아래 기준으로 역할 유형을 플레이어들별로 나누고 우선순위 지표를 다르게 해석하십시오.

            A. 캐리 라인 (Top 칼챔, Mid 메이지/암살자, Bot 원딜):
            평가 기준: KDA(특히 데스 관리), 챔피언에게 가한 피해량(DPM), 분당 골드/CS.
            평가: 딜량이 팀 내 1~2위가 아니거나 데스가 많으면 "성장 못한 캐리"로 혹평할 것.
                                                       
            B. 탱커 & 이니시에이터 (Top 탱커, Jungle 탱커, Sup 탱커):**
            최우선: 받은 피해량 + 경감된 피해량(탱킹 능력), 군중 제어(CC) 점수, 어시스트.
            평가: 데스가 다소 많더라도 어시스트와 탱킹 지표가 높으면 "든든한 방패"로 호평할 것.
                                                       
            C. 유틸리티 & 서포터 (Sup 유틸):**
            최우선: 시야 점수, 킬 관여율(KP%), 힐/보호막 양, 제어 와드 구매 수.
            평가: 시야 점수가 낮거나 데스가 많으면 "시야 없는 맛집"으로 혹평할 것.
                                                       
            D. 정글러 (Jungle 성장/갱킹):**
            최우선: 오브젝트(용/바론) 획득 기여, 킬 관여율, 초반 15분 지표.
            평가: 딜량보다는 게임 전체에 미친 영향력(라인 개입)을 중심으로 볼 것.
                                                       
                                                
            3. 분석 결과와 승패여부를 이용해서, 플레이어들의 승리/패배 기여 유형을 4가지로 나누시오
                                                       
            A. 플레이어가 잘 했고 게임을 이긴 경우 (게임을 캐리했다)
            B. 플레이어가 잘 했지만 게임을 졌다 (팀운이 좋지 않았다)
            C. 플레이어가 못 했지만 게임을 이겼다. (팀을 잘 만나서 이겼다, 버스탔다)
            D. 플레이어가 못 해서 게임을 졌다. (게임 패배에 큰 기여)
                                                       
        출력 내용  :                                            

        1. "player_keyword": (⚡ 한 단어로 플레이스타일 요약)
         - 분석 대상 플레이어의 스타일을 한 단어로 요약해서 제시. (예시: 전장의 지배자, 진영 파괴자, 최후의 보루, 상대 팀의 악몽, 기적의 역전가 등)
         - 이 내용을 누락하지 말고 꼭 제시할 것.


        2. "one_line_review": (⚡ 한줄평)
        - 분석 대상 플레이어의 활약상을 한 문장으로 요약. (등급을 부여하지 않을 것)

            4가지로 나누어진 플레이어 유형과 승리/패배 기여 유형에 따라 플레이에 대한 평가를 모두 총합해서, 
                                               
            이 플레이어에게 어울리는 한줄평을 작성한다.

            이때, 적당한 유머와 구어체를 사용해서 작성할 것.
                                                       
            예시) 원거리 딜러의 플레이어가 잘 했지만 게임을 진 경우 : 
            "혼자서 통나무를 열심히 들었지만, 팀원들이 통나무를 던지고 말았습니다."


        3. "match_flow": (🗺️ 경기 전체 흐름)
           - **예상 양상**:
               - 분석 대상 플레이아가 속한 팀을 **우리팀** 으로 두고, 속하지 않은 팀을 **상대팀**으로 둘 것.
               1. 팀별로 챔피언 조합에 따라 싸움 / 운영을 어떻게 진행해야 하는지 제시할 것.
               2. 우리팀이 상대팀을 이기기 위해서 플레이어가 맡아야 할 역할을 제시
                                                       
           - **게임의 실제 진행 내용**: 
               1. 초반 라인전 -> 중반 운영 -> 후반 한타 흐름 요약, 골드 차이와 및 승부처에 발생한 사건들을 설명해줄 것.
                                                       

        4. "skirmish_analysis": (⚔️ 교전 맥락 정밀 분석)
            **교전 장면에 대한 개관 및 요약**
                - 감지된 주요 장면({detected_moments})이 **발생하기 이전 상황**에 대해 알려줄 것(대형 오브젝트 등)을 알려줄 것.
                - 대상 플레이어가 속한 팀에 주요 장면의 **교전을 이기기 위한 핵심 포인트** 제시
                - **교전의 진행 과정 및 결과**에 대한 분석 제공
                - 각 장면별로 **[시간]**, **[배경]**(교전 트리거, 유불리), **[플레이어 코칭]**(포지션, 스킬, 포커싱, damage_received 참고), **[피드백]**(Good/Bad) 내용을 포함하여 서술.
            
            **대상 플레이어 중심 코칭 진행**
                - 본 주요 장면에서 **플레이어가 수행해야 할 역할을 제시**하고, 이를 잘 수행했는지 피드백할것
                - 이외에도 교전을 대상 **플레이어가 유리하게 진행할 수 있도록 하는 요인**에 대해 언급해주기
                                                       

        5. "play_eval": (📊 대상 플레이어의 플레이 및 아이템 평가) : 이때 긍정 및 부정적 관점에 치우치지 않을 것.
           - **역할 수행**: 딜량/탱킹/시야 지표를 바탕으로 대상 플레이어가 수행해야 할 역할을 잘 진행하였는지 평가할 것.
                                                    
           - **아이템**: 플레이어의 역할과 상대 조합을 고려해서 아이템을 적절히 구매하였는지 평가. 

        6. "team_atmosphere": (🔊 팀 분위기)
           - 핑 데이터(`pings`)를 기반으로 한 소통 및 오더 갈림 진단.
            특히 물음표핑과 위험핑이 적재적소에 사용되었는지, 아니면 아군에게 감정을 표시하기 위한 용도로 사용되었는지 확인해볼 것
            하나의 단락으로 설정할 것

        # Output Tone
        - 전문적인 e스포츠 해설가처럼 분석적이지만, 플레이어의 성장을 돕는 코치처럼 구체적이고 실용적인 조언을 하십시오.
        - 게임 관련 영어 raw data 내용을 모두 한국어로 변환하고, **영어 원문 내용은 절대 포함하지 마시오**.
        - 라이엇 API에 존재하는 모든 숫자 형태의 raw data는 실제 data dragon에 있는 내용으로 맞춘 후 제시하고, **절대 raw data가 출력되는 일은 없도록 하시오**.(예시 : 3124 -> 그림자 검)
        """)

      

    def generate_report(self, match_data: Dict, timeline_data: Dict, target_puuid: str) -> Dict:
        """
        API 데이터를 받아 JSON 분석 결과를 반환하는 메인 함수
        """
        # 1. API 데이터 전처리
        processor = RiotMatchDataProcessor(match_data, timeline_data)
        processed_context = processor.generate_context()
        
        # 타겟 플레이어 정보
        players = processed_context['match_summary']['players']
        # PUUID가 없으면 첫 번째 플레이어로 대체 (안전장치)
        target_info = next((p for p in players if p.get('puuid') == target_puuid), players[0])
        
        target_champion = target_info['championName']
        target_position = target_info['teamPosition']
        target_team = target_info['teamId']

        enemy_team_id = 200 if target_team == 100 else 100
        enemy_champs = [p['championName'] for p in players if p['teamId'] == enemy_team_id]
        enemy_champs_str = ", ".join(enemy_champs)

        # 2. 중요 장면 감지
        detector = MatchEventDetector(processed_context['timeline_flow'])
        detected_moments = detector.detect_key_moments()
        detected_moments_str = ", ".join(detected_moments)
        
        # 3. 지식(Wiki) 검색
        knowledge_text = "외부 지식 없음"
        if self.retriever:
            query = f"{target_champion} {target_position} 운영법 vs {enemy_champs_str}"
            docs = self.retriever.invoke(query)
            knowledge_text = "\n".join([f"[문서: {d.metadata.get('source', 'Wiki')}] {d.page_content}" for d in docs])

        # 4. LLM 실행
        print(f"🤖 AI 분석 시작 (Model: {LLM_MODEL}): {target_champion} ({target_position})")
        chain = self.prompt | self.llm | StrOutputParser()
        
        match_context_str = json.dumps(processed_context, ensure_ascii=False)
        
        # 토큰 제한을 고려하여 Context 길이 조절
        response_text = chain.invoke({
            "target_champion": target_champion,
            "target_position": target_position,
            "enemy_champions": enemy_champs_str,
            "detected_moments": detected_moments_str,
            "match_context": match_context_str[:30000],
            "knowledge_context": knowledge_text,
            "full_skill_dict" : full_skill_dict,
            "full_champion_dict" : full_champion_dict
            
        })

        # 5. JSON 파싱
        try:
            # Markdown 코드블럭(```json) 제거 로직
            cleaned_text = re.sub(r"^```json", "", response_text.strip(), flags=re.MULTILINE)
            cleaned_text = re.sub(r"^```", "", cleaned_text, flags=re.MULTILINE).strip()
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            print("⚠️ JSON 파싱 실패, 원본 텍스트 반환")
            return {
                "one_line_review": "분석 결과 포맷팅에 실패했습니다.",
                "match_flow": response_text
            }

# 싱글톤 인스턴스 (외부에서 import하여 사용)
rag_service = RAGService()