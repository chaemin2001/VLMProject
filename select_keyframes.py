# src/select_keyframes_from_timeseries_events.py
import csv, json
from pathlib import Path
from shutil import copy2

def load_timeseries(csv_path):
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append({
                "second": int(row["second"]),
                "fire_s": float(row.get("fire_score", 0) or 0),
                "smoke_s": float(row.get("smoke_score", 0) or 0),
            })
    rows.sort(key=lambda x: x["second"])
    return rows

def load_events(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f).get("events", [])

def to_index(rows): return {r["second"]: r for r in rows}

def best_in_window(rows, center, radius, key):
    cand = [r for r in rows if abs(r["second"] - center) <= radius]
    if not cand: return None
    return max(cand, key=lambda x: x[key])["second"]

def top_k_seconds(rows, key, k):
    return [r["second"] for r in sorted(rows, key=lambda x: x[key], reverse=True)[:k]]

def select(
    timeseries_csv, events_json, frames_dir,
    out_dir, out_csv,
    radius=5, limit=20
):
    rows = load_timeseries(timeseries_csv)
    evts = load_events(events_json)
    idx = to_index(rows)

    seconds = set()

    # 1) 시작 구간 주변에서 최고점 스냅 1장씩
    for tname, key in [("smoke_start","smoke_s"), ("fire_start","fire_s")]:
        for e in [e for e in evts if e["type"] == tname]:
            s = best_in_window(rows, e["second"], radius, key)
            if s is not None: seconds.add(s)

    # 2) 피크 & 재등장 시점
    for e in evts:
        if e["type"] in ("smoke_peak","fire_peak","smoke_reappear","fire_reappear"):
            seconds.add(e["second"])

    # 3) 점수 상위 프레임(보강)
    seconds.update(top_k_seconds(rows, "fire_s", 3))
    seconds.update(top_k_seconds(rows, "smoke_s", 3))

    # 정렬/자르기
    chosen = sorted(seconds)[:limit]

    # 저장
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["second","fire_score","smoke_score","file"])
        for s in chosen:
            src = Path(frames_dir) / f"{s:04d}.jpg"
            dst = out_dir / src.name
            if src.exists(): copy2(src, dst)
            row = idx.get(s, {"fire_s":0.0,"smoke_s":0.0})
            w.writerow([s, row["fire_s"], row["smoke_s"], dst.name])

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--video_id", required=True)
    ap.add_argument("--frames_dir", required=True)
    ap.add_argument("--timeseries_csv", required=True)
    ap.add_argument("--events_json", required=True)
    ap.add_argument("--out_root", default="outputs")
    ap.add_argument("--radius", type=int, default=5)
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    out_dir = f"{args.out_root}/{args.video_id}/keyframes"
    out_csv = f"{args.out_root}/{args.video_id}/keyframes.csv"

    select(
        timeseries_csv=args.timeseries_csv,
        events_json=args.events_json,
        frames_dir=args.frames_dir,
        out_dir=out_dir,
        out_csv=out_csv,
        radius=args.radius,
        limit=args.limit
    )
