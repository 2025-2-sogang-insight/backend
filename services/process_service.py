import json
from services.riot_service import get_match_detail, get_match_timeline

class RiotMatchDataProcessor:
    def __init__(self, match_data, timeline_data):
        self.match = match_data.get('info', {})
        self.timeline = timeline_data.get('info', {})
        self.participants_map = {p['participantId']: p['championName'] for p in self.match.get('participants', [])}

    def get_participant_name(self, p_id):
        """참가자 ID를 챔피언 이름으로 변환 (가독성 향상)"""
        return self.participants_map.get(p_id, f"Unknown({p_id})")

    def process_match_summary(self):
        """MATCH 데이터(v5/match)에서 핵심 정보 추출"""
        
        # 1. 경기 개요 (Metadata & Result)
        game_overview = {
            "gameId": self.match.get('gameId'),
            "gameDuration": self.match.get('gameDuration'),  # 초 단위
            "gameMode": self.match.get('gameMode'),
            "gameVersion": self.match.get('gameVersion'),
            "teams": []
        }

        # 2. 팀 데이터 (Objectives, Bans, Win/Loss)
        for team in self.match.get('teams', []):
            team_info = {
                "teamId": team['teamId'],
                "win": team['win'],
                "bans": [b['championId'] for b in team.get('bans', [])], # 챔피언 ID 리스트
                "objectives": team.get('objectives', {}), # 드래곤, 바론, 타워, 억제기 등
                "total_kills": team.get('objectives', {}).get('champion', {}).get('kills', 0)
            }
            game_overview['teams'].append(team_info)

        # 3. 플레이어 상세 퍼포먼스 (Participants)
        player_stats = []
        for p in self.match.get('participants', []):
            stats = {
                "participantId": p['participantId'],
                "championName": p['championName'],
                "teamPosition": p.get('teamPosition'),
                "teamId": p['teamId'],
                
                # A. 역할 및 빌드 (Draft & Roles)
                "runes": p.get('perks', {}).get('styles', []), # 핵심 룬/보조 룬
                "summonerSpells": [p.get('summoner1Id'), p.get('summoner2Id')],
                "items": [p.get(f'item{i}') for i in range(7)], # 최종 아이템 7개
                
                # B. 성장 및 전투 (Performance)
                "kda": f"{p['kills']}/{p['deaths']}/{p['assists']}",
                "goldEarned": p['goldEarned'],
                "totalMinionsKilled": p['totalMinionsKilled'] + p['neutralMinionsKilled'], # CS 합계
                "champLevel": p['champLevel'],
                "totalDamageDealtToChampions": p['totalDamageDealtToChampions'],
                "damageSelfMitigated": p['damageSelfMitigated'],
                "totalDamageTaken": p['totalDamageTaken'],
                "totalHeal": p['totalHeal'],
                "totalTimeCCDealt": p['totalTimeCCDealt'],
                
                # C. 생존 및 시야
                "totalTimeSpentDead": p['totalTimeSpentDead'],
                "visionScore": p['visionScore'],
                "wardsPlaced": p['wardsPlaced'],
                "detectorWardsPlaced": p['detectorWardsPlaced'],
                
                # D. 교전 맥락 보조 데이터
                "largestMultiKill": p['largestMultiKill'],
                "longestTimeSpentLiving": p['longestTimeSpentLiving'],
                "spellCasts": {
                    "Q": p.get('spell1Casts'), "W": p.get('spell2Casts'),
                    "E": p.get('spell3Casts'), "R": p.get('spell4Casts'),
                    "Summoner1": p.get('summoner1Casts'), "Summoner2": p.get('summoner2Casts')
                },
                
                # E. 팀 분위기 (Pings)
                "pings": {
                    "command": p.get('commandPings', 0),
                    "allIn": p.get('allInPings', 0),
                    "push": p.get('pushPings', 0),
                    "danger": p.get('dangerPings', 0),
                    "getBack": p.get('getBackPings', 0),
                    "enemyMissing": p.get('enemyMissingPings', 0), # 정치질 지표 활용 가능
                    "assistMe": p.get('assistMePings', 0),
                    "onMyWay": p.get('onMyWayPings', 0),
                    "needVision": p.get('needVisionPings', 0),
                    "visionCleared": p.get('visionClearedPings', 0)
                }
            }
            player_stats.append(stats)

        return {"overview": game_overview, "players": player_stats}

    def process_timeline_summary(self):
        """TIMELINE 데이터(v5/match/timeline)에서 흐름 및 이벤트 추출"""
        
        frames_summary = []
        
        # 분석에 필요한 핵심 이벤트 타입 정의
        TARGET_EVENTS = {
            'CHAMPION_KILL', 'ELITE_MONSTER_KILL', 'BUILDING_KILL', 
            'TURRET_PLATE_DESTROYED', 'ITEM_PURCHASED', 'SKILL_LEVEL_UP',
            'WARD_PLACED', 'WARD_KILL'
        }

        for frame in self.timeline.get('frames', []):
            timestamp = frame['timestamp']
            minute = int(timestamp / 60000) # 분 단위 변환
            
            # 1. 해당 시간대의 플레이어 상태 (성장, 위치, 체력)
            player_status = {}
            for p_id_str, p_data in frame.get('participantFrames', {}).items():
                p_id = int(p_id_str)
                player_status[self.get_participant_name(p_id)] = {
                    "totalGold": p_data['totalGold'],
                    "xp": p_data['xp'],
                    "level": p_data['level'],
                    "minions": p_data['minionsKilled'],
                    "jungleMinions": p_data['jungleMinionsKilled'],
                    "position": p_data.get('position', {}), # x, y 좌표
                    "health": p_data['championStats']['health'],
                    "power": p_data['championStats']['power'] # 마나/기력
                }

            # 2. 해당 시간대에 발생한 주요 이벤트 필터링
            events = []
            for event in frame.get('events', []):
                if event['type'] not in TARGET_EVENTS:
                    continue
                
                # 이벤트별 핵심 데이터만 정제
                event_summary = {"type": event['type'], "timestamp": event['timestamp']}
                
                if event['type'] == 'CHAMPION_KILL':
                    event_summary.update({
                        "killer": self.get_participant_name(event.get('killerId')),
                        "victim": self.get_participant_name(event.get('victimId')),
                        "assists": [self.get_participant_name(aid) for aid in event.get('assistingParticipantIds', [])],
                        "position": event.get('position'),
                        # 피해 상세 로그 (중요: 누가 스킬을 썼는가)
                        "damage_received": [
                            {
                                "attacker": dmg.get('name'),
                                "spell": dmg.get('spellName'),
                                "type": dmg.get('type')
                            } for dmg in event.get('victimDamageReceived', [])
                        ]
                    })
                
                elif event['type'] in ['ELITE_MONSTER_KILL', 'BUILDING_KILL']:
                    event_summary.update({
                        "killer": self.get_participant_name(event.get('killerId')),
                        "teamId": event.get('teamId'), # 어느 팀이 먹었나
                        "monsterType": event.get('monsterType'),
                        "towerType": event.get('towerType'),
                        "laneType": event.get('laneType'),
                        "position": event.get('position')
                    })
                
                elif event['type'] == 'ITEM_PURCHASED':
                    event_summary.update({
                        "participant": self.get_participant_name(event.get('participantId')),
                        "itemId": event.get('itemId')
                    })
                
                elif event['type'] == 'SKILL_LEVEL_UP':
                    event_summary.update({
                        "participant": self.get_participant_name(event.get('participantId')),
                        "skillSlot": event.get('skillSlot'),
                        "levelUpType": event.get('levelUpType')
                    })
                
                elif event['type'] in ['WARD_PLACED', 'WARD_KILL']:
                    event_summary.update({
                        "actor": self.get_participant_name(event.get('creatorId') or event.get('killerId')),
                        "wardType": event.get('wardType')
                    })

                events.append(event_summary)

            frames_summary.append({
                "minute": minute,
                "player_status": player_status,
                "events": events
            })

        return frames_summary

    def generate_rag_context(self):
        """최종 RAG 모델 입력용 데이터 생성"""
        return {
            "match_summary": self.process_match_summary(),
            "timeline_flow": self.process_timeline_summary()
        }

def get_rag_json(match_id: str):
    """PUUID와 MatchId를 통해 RAG용 JSON 데이터를 생성"""
    match_data = get_match_detail(match_id)
    timeline_data = get_match_timeline(match_id)
    
    if not match_data or not timeline_data:
        return None
        
    processor = RiotMatchDataProcessor(match_data, timeline_data)
    rag_context = processor.generate_rag_context()
    
    return rag_context
