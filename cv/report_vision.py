import google.generativeai as genai
import json
import os

# 1. Gemini API 키 설정 (본인의 API 키로 교체하세요)
API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=API_KEY)

# 2. 모델 설정
model = genai.GenerativeModel('gemini-2.5-flash')

def load_json_content(file_path):
    if not os.path.exists(file_path):
        return None
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_target_player_info(match_data):
    """match_analysis.json에서 타겟 플레이어 정보를 추출합니다."""
    # 1순위: analysis_target 필드 확인
    if "analysis_target" in match_data:
        return match_data["analysis_target"]
    
    # 2순위: is_target: true인 플레이어 검색
    for team in ["blue_team", "red_team"]:
        for player in match_data.get(team, []):
            if player.get("is_target"):
                # 팀 정보 추가
                player["team_color"] = "Blue" if team == "blue_team" else "Red"
                return player
    return None

def analyze_personal_performance():
    # 3. 데이터 로드
    match_data = load_json_content("match_analysis.json")
    timeline_data = load_json_content("fight_timeline_api.json")
    tracking_data = load_json_content("all_results.json") # 텍스트로 변환하여 전송

    if not match_data:
        print("❌ match_analysis.json 파일을 찾을 수 없습니다.")
        return

    # 타겟 플레이어 식별
    target_info = get_target_player_info(match_data)
    if not target_info:
        print("❌ 분석 대상(Target Player)을 찾을 수 없습니다. 'is_target': true를 확인해주세요.")
        return

    print(f"🎯 분석 대상: {target_info['champion']} ({target_info['role']}) - {target_info.get('team_color', 'Unknown')} Team")

    # 4. 프롬프트 구성 (코칭 및 피드백 중심)
    prompt = f"""
    너는 League of Legends(LoL) 프로팀의 **개인 전담 코치(Personal Coach)**야.
    이번 한타(Teamfight) 데이터를 분석해서, **Target Player**에게 구체적인 피드백을 줘야 해.

    ### 🎯 Target Player 정보:
    - **Champion**: {target_info['champion']}
    - **Role**: {target_info['role']} (이 역할의 핵심 임무를 기준으로 평가할 것)
    - **Team**: {target_info.get('team_color')} Team

    ### 📂 입력 데이터:
    1. **Match Context (match_analysis.json)**: {json.dumps(match_data, ensure_ascii=False)}
    2. **Events (fight_timeline_api.json)**: {json.dumps(timeline_data, ensure_ascii=False)}
    3. **Tracking (all_results.json)**: {json.dumps(tracking_data, ensure_ascii=False)}

    ### 📝 분석 가이드라인:
    단순한 상황 중계가 아니라, **철저히 Target Player의 시점**에서 분석해줘.
    - **포지셔닝 평가**: {target_info['role']}로서 위치 선정이 적절했는가? (예: 원딜이면 카이팅 거리 유지, 이니시에이터면 진입 각)
    - **반응 속도**: 위협적인 스킬이나 적의 진입에 대해 적절히 반응했는가?
    - **기여도**: 킬 관여나 생존 여부를 통해 한타 승패에 어떤 영향을 끼쳤는가?

    ### 📤 출력 포맷 (JSON Only):
    반드시 아래 JSON 구조로만 응답해.
    {{
      "analysis_target": "{target_info['champion']}",
      "match_analysis_version": "2.0",
      "timestamp_mapping": {{ "video_fps": 30 }},
      "sections": [
        {{
          "section_id": 1,
          "phase": "단계 (예: 진입 전, 교전 중, 마무리)",
          "time_range_sec": [시작초, 끝초],
          "situation_summary": "전체적인 전황 요약 (1문장)",
          "target_performance_feedback": "타겟 플레이어의 행동에 대한 구체적인 코칭. '잘했다/못했다'를 판단하고 그 이유를 설명. (예: 'Vi가 들어올 때 침착하게 뒷무빙을 쳐서 생존한 판단이 아주 좋았습니다.')",
          "action_score": 85,  // 이 구간 플레이 점수 (0~100)
          "key_events_related": [
            {{
               "timestamp_game": 12345,
               "description": "타겟 플레이어와 직접 관련된 이벤트 (킬/데스/어시스트 혹은 주요 회피)"
            }}
          ]
        }}
      ],
      "overall_review": "한타 전체에 대한 총평 한 줄 요약"
    }}
    """

    print("🤖 Gemini 코치가 데이터를 분석 중입니다... (잠시만 기다려주세요)")
    
    # 5. API 호출
    try:
        response = model.generate_content(prompt)
        result_text = response.text.replace("```json", "").replace("```", "").strip()
        
        # 결과 저장
        result_json = json.loads(result_text)
        
        output_filename = "personal_coaching_result.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(result_json, f, indent=2, ensure_ascii=False)
            
        print(f"✅ 피드백 생성 완료! '{output_filename}' 파일을 확인하세요.")
        print("\n--- [Coaching Preview] ---")
        print(f"총평: {result_json.get('overall_review', 'N/A')}")
        
    except Exception as e:
        print(f"❌ 분석 중 오류 발생: {e}")
        # 디버깅용: 실패 시 원본 응답 출력
        if 'response' in locals():
            print("Raw Response:", response.text)

if __name__ == "__main__":
    analyze_personal_performance()