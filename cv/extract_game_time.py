import cv2
import google.generativeai as genai
from PIL import Image
import re
import os
from dotenv import load_dotenv

# .env 파일 로드 (같은 폴더에 .env 파일이 있다면)
load_dotenv()

# ==========================================
# [설정 구역] 여기에 영상 파일명과 키를 입력하세요
# ==========================================
VIDEO_FILENAME = "카이사판.mp4"  # 분석할 영상 파일명 (같은 폴더에 있어야 함)
MY_API_KEY = os.getenv("GOOGLE_API_KEY") # .env가 없으면 여기에 직접 "AIza..." 키를 문자열로 넣으세요
# ==========================================

class GeminiTimeReader:
    def __init__(self, api_key=None):
        key = api_key if api_key else MY_API_KEY
        
        if not key:
            print("❌ 오류: API Key가 설정되지 않았습니다. 코드 상단의 MY_API_KEY에 키를 입력하거나 .env 파일을 확인하세요.")
            return

        genai.configure(api_key=key)
        try:
            self.model = genai.GenerativeModel('gemini-2.5-flash')
        except Exception as e:
            print(f"모델 초기화 오류: {e}")

    def get_frame_at_index(self, video_path, frame_index):
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        cap.release()
        
        if not ret: return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)

    def extract_game_times(self, video_path):
        if not os.path.exists(video_path):
            print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
            return None

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames == 0:
            print("영상을 읽을 수 없습니다.")
            return None
        cap.release()

        # 시작/끝 프레임 추출
        start_img = self.get_frame_at_index(video_path, 60) # 시작 후 1~2초
        end_idx = max(0, total_frames - 180) # 끝나기 3~5초 전
        end_img = self.get_frame_at_index(video_path, end_idx) 

        if not start_img or not end_img:
            print("프레임 추출 실패")
            return None

        print("🔍 Gemini에게 시간을 물어보는 중...")
        prompt = """
        I will provide two screenshots from a League of Legends gameplay video.
        Image 1: The beginning of the video.
        Image 2: The end of the video.
        Location Hints:
        1. First, look at the **top-right corner** of the screen.
        2. If the timer is not there (e.g., spectator mode), look at the **top-center area**, slightly below the very top edge (usually under the score board)
        Return JSON: {"start_time_str": "MM:SS", "end_time_str": "MM:SS"}
        """

        try:
            response = self.model.generate_content([prompt, start_img, end_img])
            return self._parse_response(response.text)
        except Exception as e:
            print(f"API 호출 오류: {e}")
            return None

    def _parse_response(self, text):
        matches = re.findall(r'(\d+):(\d+)', text)
        if len(matches) < 2: return None
        
        def to_seconds(match):
            return int(match[0]) * 60 + int(match[1])

        return {
            "start_seconds": to_seconds(matches[0]),
            "end_seconds": to_seconds(matches[1])
        }




import requests
import json
import os
from dotenv import load_dotenv

# .env 로드 (API KEY)
load_dotenv()

class RiotTimelineSlicer:
    def __init__(self, api_key, region_route="asia"):
        """
        region_route: 'asia' (KR, JP), 'americas', 'europe' 등
        Match V5는 지역(Continent) 단위 라우팅을 사용합니다.
        """
        self.api_key = api_key
        self.base_url = f"https://{region_route}.api.riotgames.com"
        self.headers = {
            "X-Riot-Token": self.api_key
        }

    def fetch_full_timeline(self, match_id):
        """API에서 전체 타임라인 JSON을 받아옵니다."""
        url = f"{self.base_url}/lol/match/v5/matches/{match_id}/timeline"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API 요청 실패: {e}")
            return None

    def slice_data(self, timeline_json, start_sec, end_sec):
        """
        OCR로 얻은 start_sec ~ end_sec 사이의 데이터만 추출합니다.
        """
        if not timeline_json: return None

        # 1. 초 -> 밀리초 변환
        start_ms = start_sec * 1000
        end_ms = end_sec * 1000
        
        # 2. 검색 범위를 줄이기 위해 '분(Minute)' 인덱스 계산
        # 예: 15분 30초 시작이면 frames[15]부터 보면 됨
        start_idx = int(start_sec // 60)
        end_idx = int(end_sec // 60)
        
        frames = timeline_json['info']['frames']
        max_idx = len(frames) - 1
        
        # 결과 담을 컨테이너
        sliced_result = {
            "interval_seconds": (start_sec, end_sec),
            "events": [],            # 구간 내 발생한 사건들 (Kill, Ward, Item...)
            "participant_frames": [] # 구간 내 챔피언 상태 (위치, 골드, XP 등 - 1분 주기)
        }

        # 3. 필요한 프레임만 순회
        # end_idx + 1을 해주는 이유는 Python slice가 마지막을 포함 안하기 때문, 
        # 그리고 끝나는 시간의 '분' 데이터도 필요할 수 있음.
        search_range = range(start_idx, min(end_idx + 2, max_idx + 1))

        for i in search_range:
            frame = frames[i]
            
            # (1) Events 필터링 (정밀함: 밀리초 단위)
            for event in frame['events']:
                ts = event['timestamp']
                if start_ms <= ts <= end_ms:
                    # 보기 좋게 '초(sec)' 필드 추가 (선택사항)
                    event['timestamp_sec'] = ts / 1000 
                    sliced_result['events'].append(event)
            
            # (2) ParticipantFrames 가져오기 (1분 간격 스냅샷)
            # 이 데이터는 해당 분(Minute)의 '0초' 시점 데이터입니다.
            # 영상 구간에 포함되거나 걸쳐있는 프레임 정보를 저장합니다.
            frame_data = {
                "timestamp": frame['timestamp'], # 예: 900000 (15분)
                "timestamp_sec": frame['timestamp'] / 1000,
                "participants": frame['participantFrames'] # 1~10번 챔피언 정보
            }
            sliced_result['participant_frames'].append(frame_data)

        return sliced_result




# --- 메인 실행부 (여기가 바뀌었습니다) ---
if __name__ == "__main__":
    # 클래스 생성
    reader = GeminiTimeReader()
    
    # 설정해둔 파일명으로 바로 실행
    print(f"▶ 분석 시작: {VIDEO_FILENAME}")
    result = reader.extract_game_times(VIDEO_FILENAME)
    
    if result:
        print("\n" + "="*30)
        print("   ✅ 분석 성공! (결과)")
        print("="*30)
        print(f"1. 영상 시작 시 게임 시간 : {result['start_seconds']}초")
        print(f"2. 영상 종료 시 게임 시간 : {result['end_seconds']}초")
        print("-" * 30)
        print(f"★ 동기화 공식: API 타임라인 조회 시 [{result['start_seconds']}]초를 더하세요.")
        print("="*30)
    else:
        print("\n❌ 분석 실패 (시간을 읽지 못했습니다)")


    # --- 사용 예시 ---
if __name__ == "__main__":
    # 1. 설정
    API_KEY = os.getenv("RIOT_API_KEY") # .env에 RIOT_API_KEY 설정 필요
    MATCH_ID = "KR_7971051219" # 테스트할 매치 ID

    
    # 2. OCR에서 구한 시간 (예시: 영상이 게임 시간 15분 30초 ~ 15분 50초 구간임)
    OCR_START_SEC = result['start_seconds']  # 15분 30초
    OCR_END_SEC = result['end_seconds']    # 15분 50초
    
    

    

    slicer = RiotTimelineSlicer(api_key=API_KEY, region_route="asia")
    
    print(f"🚀 데이터 가져오는 중... MatchID: {MATCH_ID}")
    full_timeline = slicer.fetch_full_timeline(MATCH_ID)
    
    if full_timeline:
        print(f"✂️ 데이터 자르는 중... ({OCR_START_SEC}초 ~ {OCR_END_SEC}초)")
        
        result = slicer.slice_data(full_timeline, OCR_START_SEC, OCR_END_SEC)
        
        if result:
            print(f"\n▶ 3단계: 파일 저장")
            OUTPUT_FILENAME = "fight_timeline_api.json"
            try:
                with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
                    # ensure_ascii=False: 한글 등 유니코드 깨짐 방지
                    # indent=4: 들여쓰기로 보기 좋게 저장
                    json.dump(result, f, indent=4, ensure_ascii=False)
                
                print(f"   💾 저장 완료! 파일명: {OUTPUT_FILENAME}")
                print(f"   📊 이벤트 개수: {len(result['events'])}개")
                print(f"   📌 프레임 개수: {len(result['participant_frames'])}개")
                
            except Exception as e:
                print(f"   ❌ 파일 저장 중 오류 발생: {e}")
        else:
            print("   ⚠️ 슬라이싱된 데이터가 없습니다.")
    else:
        print("❌ 타임라인 데이터를 받아오지 못했습니다.")
        # 결과 출력
        print("\n" + "="*40)
        print(f"   📊 분석 구간 데이터 ({len(result['events'])}개 이벤트)")
        print("="*40)
        
        # 1. 이벤트 출력
        for event in result['events']:
            # 킬 이벤트만 예쁘게 출력해보기
            if event['type'] == 'CHAMPION_KILL':
                print(f"[{event['timestamp_sec']:.1f}s] 💀 킬 발생! (Killer: {event['killerId']} -> Victim: {event['victimId']})")
            else:
                print(f"[{event['timestamp_sec']:.1f}s] ℹ️ {event['type']}")

        # 2. 위치 데이터 확인
        print("-" * 40)
        print(f"📌 참조된 위치 프레임(스냅샷) 개수: {len(result['participant_frames'])}개")
        for pf in result['participant_frames']:
             print(f" - {int(pf['timestamp_sec']/60)}분 0초 데이터")