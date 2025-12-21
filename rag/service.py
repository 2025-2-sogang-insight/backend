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

        1. "one_line_review": (⚡ 한줄평)
           - 승패 요인과 대상 플레이어의 활약상을 한 문장으로 요약. (S/A/B/C 등급 부여 포함)

        2. "match_flow": (🗺️ 경기 전체 흐름)
           - **예상 양상**: 챔피언 상성 및 조합에 따른 이상적인 플레이 방향.
           - **실제 진행**: 초반 라인전 -> 중반 운영 -> 후반 한타 흐름 요약. 골드 차이와 승부처 언급.

        3. "skirmish_analysis": (⚔️ 교전 맥락 정밀 분석)
           - 감지된 주요 장면({detected_moments}) 중 가장 승패에 영향이 컸던 2~3가지를 골라 상세 분석.
           - 각 장면별로 **[시간]**, **[배경]**(교전 트리거, 유불리), **[플레이어 코칭]**(포지션, 스킬, 포커싱, damage_received 참고), **[피드백]**(Good/Bad) 내용을 포함하여 서술.

        4. "play_eval": (📊 플레이 및 아이템 평가)
           - **역할 수행**: 딜량/탱킹/시야 지표를 바탕으로 1인분 여부 판단.
           - **아이템**: 상대 조합 대비 아이템 빌드의 효율성 평가.

        5. "team_atmosphere": (🔊 팀 분위기)
           - 핑 데이터(`pings`)를 기반으로 한 소통 및 오더 갈림 진단.

        # Output Tone
        - 전문적인 e스포츠 해설가처럼 분석적이지만, 플레이어의 성장을 돕는 코치처럼 구체적이고 실용적인 조언을 하십시오.
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
            "knowledge_context": knowledge_text
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