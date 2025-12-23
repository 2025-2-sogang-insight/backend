# ==========================================
# 1. 환경 설정 및 라이브러리 설치
# ==========================================
try:
    import ultralytics
except ImportError:
    print("YOLO 라이브러리 설치 중...")
    !pip install ultralytics -q

import cv2
import os
import json
import shutil
from ultralytics import YOLO

# ==========================================
# 2. 사용자 설정
# ==========================================
VIDEO_FILE = "카이사판.mp4"   # 분석할 영상 파일
MODEL_FILE = "best.pt"     # 학습된 모델 파일
OUTPUT_DIR = "outputs"     # 결과물 저장 폴더
TARGET_CLASSES = [10, 11, 12] # 분석할 클래스 ID

# ==========================================
# 3. 비디오 처리 및 저장 로직
# ==========================================
def process_video_save_mode(video_path, model_path, output_dir):
    # 폴더 초기화
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # 모델 로드
    model = YOLO(model_path)

    print(f"🎬 영상 분석 시작: {video_path}")
    print(f"💾 save=True 모드: 영상에 박스를 그려서 저장합니다.")

    results = model.track(
        source=video_path,
        save=True,
        stream=True,
        persist=True,
        classes=TARGET_CLASSES,
        verbose=False
    )

    # -------------------------------------------------------
    # [변경점 1] 모든 프레임 데이터를 담을 리스트 생성
    # -------------------------------------------------------
    all_frame_results = []

    # 프레임별로 돌면서 데이터 수집
    for frame_idx, result in enumerate(results):
        current_frame_objects = [] # 현재 프레임에서 발견된 객체들

        if result.boxes:
            for box in result.boxes:
                # 좌표 및 정보 추출
                cls = int(box.cls[0])
                x, y, w, h = box.xywh[0].tolist()

                # y좌표 보정
                y = y + 170

                conf = float(box.conf[0])
                track_id = int(box.id[0]) if box.id is not None else -1

                # 객체 정보 담기
                current_frame_objects.append({
                    "track_id": track_id,
                    "class_id": cls,
                    "x_center": round(x, 2),
                    "y_center": round(y, 2),
                    "width": round(w, 2),
                    "height": round(h, 2),
                    "confidence": round(conf, 2)
                })

        # -------------------------------------------------------
        # [변경점 2] 현재 프레임 정보를 전체 리스트에 추가 (파일 저장 X)
        # -------------------------------------------------------
        all_frame_results.append({
            "frame_id": frame_idx,
            "detections": current_frame_objects
        })

        # 진행 상황 출력 (50프레임마다)
        if frame_idx % 50 == 0:
            print(f"Processing frame {frame_idx}...")

    # -------------------------------------------------------
    # [변경점 3] 반복문이 끝난 후 하나의 JSON 파일로 저장
    # -------------------------------------------------------
    print("\n✅ 분석 완료! 하나의 JSON 파일로 저장 중...")
    json_path = os.path.join(output_dir, "all_results.json")

    with open(json_path, 'w') as f:
        json.dump(all_frame_results, f, indent=4)

    print(f"📄 JSON 저장 완료: {json_path}")


    # ---------------------------------------------------------
    # YOLO가 저장한 영상을 결과 폴더로 이동
    # ---------------------------------------------------------
    print("📦 저장된 영상을 결과 폴더로 이동 중...")
    try:
        base_run_path = 'runs/detect'
        if os.path.exists(base_run_path):
            subfolders = [os.path.join(base_run_path, d) for d in os.listdir(base_run_path) if os.path.isdir(os.path.join(base_run_path, d))]
            if subfolders:
                latest_folder = max(subfolders, key=os.path.getmtime)
                video_files = [f for f in os.listdir(latest_folder) if f.endswith(('.avi', '.mp4'))]

                if video_files:
                    src_video = os.path.join(latest_folder, video_files[0])
                    dst_video = os.path.join(output_dir, "result_video.avi")
                    shutil.copy(src_video, dst_video)
                    print(f"   영상 이동 완료: {dst_video}")
                else:
                    print("⚠️ 경고: 영상 파일을 찾을 수 없습니다.")
        else:
            print("⚠️ 경고: runs/detect 폴더가 없습니다.")

    except Exception as e:
        print(f"⚠️ 영상 이동 중 오류 발생: {e}")

    # ==========================================
    # 4. 결과 압축 (JSON + Video)
    # ==========================================
    print("📦 전체 결과를 압축하는 중...")
    shutil.make_archive("final_results", 'zip', output_dir)
    print(f"🎉 압축 완료: final_results.zip")
    print("   (이 파일 안에 'all_results.json'과 결과 영상이 들어있습니다.)")

# ==========================================
# 5. 실행
# ==========================================
if __name__ == "__main__":
    process_video_save_mode(VIDEO_FILE, MODEL_FILE, OUTPUT_DIR)