# scripts/timeseries_to_events.py
import csv, json
from statistics import mean

def load_timeseries(csv_path):
    secs, f, s = [], [], []
    with open(csv_path, "r", encoding="utf-8") as fobj:
        r = csv.DictReader(fobj)
        for row in r:
            secs.append(int(row["second"]))
            f.append(float(row.get("fire_score", 0) or 0))
            s.append(float(row.get("smoke_score", 0) or 0))
    return secs, f, s

def moving_avg(seq, window=5):
    if window <= 1:
        return seq[:]
    out, n = [], len(seq)
    half = window // 2
    for i in range(n):
        a, b = max(0, i - half), min(n, i + half + 1)
        out.append(mean(seq[a:b]))
    return out

def first_crossing(seq, thresh):
    for i, v in enumerate(seq):
        if v >= thresh:
            return i
    return None

def local_peaks(seq):
    peaks = []
    for i in range(1, len(seq)-1):
        if seq[i] > seq[i-1] and seq[i] >= seq[i+1]:
            peaks.append(i)
    return peaks

def to_events(csv_path, out_json, window=5, fire_thr=0.3, smoke_thr=0.3):
    secs, fire, smoke = load_timeseries(csv_path)
    fire_s = moving_avg(fire, window)
    smoke_s = moving_avg(smoke, window)

    events = []
    fs = first_crossing(fire_s, fire_thr)
    ss = first_crossing(smoke_s, smoke_thr)
    if ss is not None: events.append({"type":"smoke_start","second":secs[ss]})
    if fs is not None: events.append({"type":"fire_start","second":secs[fs]})

    for i in local_peaks(smoke_s):
        events.append({"type":"smoke_peak","second":secs[i],"score":round(smoke_s[i],4)})
    for i in local_peaks(fire_s):
        events.append({"type":"fire_peak","second":secs[i],"score":round(fire_s[i],4)})

    events.sort(key=lambda x: x["second"])
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"events":events}, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="timeseries.csv")
    ap.add_argument("--out_json", required=True, help="events.json")
    ap.add_argument("--smooth_window", type=int, default=5)
    ap.add_argument("--fire_thresh", type=float, default=0.3)
    ap.add_argument("--smoke_thresh", type=float, default=0.3)
    args = ap.parse_args()

    to_events(
        csv_path=args.csv,
        out_json=args.out_json,
        window=args.smooth_window,
        fire_thr=args.fire_thresh,
        smoke_thr=args.smoke_thresh
    )
