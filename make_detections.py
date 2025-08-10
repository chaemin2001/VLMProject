# scripts/make_detections_from_timeseries.py
import csv, json
from pathlib import Path

def csv_to_detections(csv_path, out_jsonl, out_json=None):
    items = []
    with open(csv_path, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            sec = int(row["second"])
            fire = float(row.get("fire_score", 0) or 0)
            smoke = float(row.get("smoke_score", 0) or 0)
            dets = []
            if smoke > 0:
                dets.append({"cls":"smoke","conf":smoke})
            if fire > 0:
                dets.append({"cls":"fire","conf":fire})
            items.append({
                "image": f"{sec:04d}.jpg",
                "second": sec,
                "detections": dets
            })

    # JSONL
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")

    # (옵션) JSON 배열
    if out_json:
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="timeseries.csv")
    ap.add_argument("--out_jsonl", required=True, help="detections.jsonl")
    ap.add_argument("--as_json", action="store_true", help="also write detections.json")
    args = ap.parse_args()

    out_json = None
    if args.as_json:
        p = Path(args.out_jsonl)
        out_json = str(p.with_suffix(".json"))
    csv_to_detections(args.csv, args.out_jsonl, out_json)
