# src/run_vlm_timeline.py
import csv, json
from pathlib import Path
from prompt_templates import system_prompt_ko, user_prompt_from_keyframes

# === (선택) 한 가지 모델만 먼저 연결해서 시작하세요. ===
# from models.qwen2vl_infer import VLModel as Model
# 또는
# from models.llava_infer import VLModel as Model

# 일단 기본은 Qwen2-VL 어댑터를 쓰는 것으로 가정 (필요시 위 import를 바꾸세요)
from models.qwen2vl_infer import VLModel as Model

def read_keyframes_csv(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    rows.sort(key=lambda x: int(x["second"]))
    return rows

def run(video_id, keyframes_dir, keyframes_csv, events_json, out_dir):
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    # 1) 데이터 로드
    with open(events_json, "r", encoding="utf-8") as f:
        events = json.load(f)
    kf_rows = read_keyframes_csv(keyframes_csv)
    images = [str(Path(keyframes_dir) / r["file"]) for r in kf_rows]

    # 2) 프롬프트 구성
    sys_prompt = system_prompt_ko()
    user_prompt = user_prompt_from_keyframes(video_id, events, kf_rows)

    # 3) 모델 로드 및 추론
    model = Model()  # 모델 초기화(어댑터에 따라 가중치 로드 등)
    result = model.infer(images=images, system_prompt=sys_prompt, user_prompt=user_prompt)

    # 4) 저장
    (out_dir / "report_raw.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # Markdown 본문이 result 안에 없다면, 간단히 user_prompt + 모델 답변 텍스트를 저장
    md = result.get("markdown") or result.get("text") or ""
    (out_dir / "report.md").write_text(md, encoding="utf-8")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video_id", required=True)
    ap.add_argument("--keyframes_dir", required=True)   # outputs/<video_id>/keyframes
    ap.add_argument("--keyframes_csv", required=True)   # outputs/<video_id>/keyframes.csv
    ap.add_argument("--events_json", required=True)     # data/<video_id>/events.json
    ap.add_argument("--out_dir", required=True)         # outputs/<video_id>
    args = ap.parse_args()

    run(
        video_id=args.video_id,
        keyframes_dir=args.keyframes_dir,
        keyframes_csv=args.keyframes_csv,
        events_json=args.events_json,
        out_dir=args.out_dir
    )
