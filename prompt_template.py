# src/prompt_templates.py
def system_prompt_ko():
    return (
        "당신은 화재 조사 보고관입니다. 다음 규칙을 따르세요.\n"
        "1) 사실 위주로 작성하고 과장하지 말 것\n"
        "2) 각 주장 끝에 [근거:t=MM:SS] 형태로 타임스탬프 근거를 표시할 것\n"
        "3) 출력은 JSON과 Markdown 두 개를 함께 제공: "
        "JSON에는 'timeline'(이벤트 배열), 'summary', 'recommendations' 키를 포함\n"
        "Markdown에는 '사건 개요/타임라인/주요 장면/관찰/권고' 섹션 포함\n"
    )

def user_prompt_from_keyframes(video_id, events, keyframe_rows):
    # events: events.json(dict), keyframe_rows: list of dict from keyframes.csv
    # 간단한 컨텍스트 문자열 생성
    lines = [f"[비디오]: {video_id}"]
    # 이벤트 요약
    evt_lines = []
    for e in events.get("events", []):
        t = e["second"]
        mm, ss = divmod(int(t), 60)
        evt_lines.append(f"- {e['type']} @ {mm:02d}:{ss:02d}")
    if evt_lines:
        lines.append("[이벤트 후보]\n" + "\n".join(evt_lines))
    # 키프레임 요약
    kf_lines = []
    for r in keyframe_rows:
        t = int(r["second"])
        mm, ss = divmod(t, 60)
        kf_lines.append(
            f"- t={mm:02d}:{ss:02d}, fire={float(r['fire_score']):.2f}, "
            f"smoke={float(r['smoke_score']):.2f}"
        )
    lines.append("[키프레임 요약]\n" + "\n".join(kf_lines))

    # 지시
    lines.append(
        "\n[지시]\n"
        "첨부된 이미지(시간순)를 근거로 타임라인을 재구성하고, "
        "각 진술 끝에 [근거:t=MM:SS]를 붙이세요. "
        "연기→불꽃 전이, 피크, 재등장 여부를 중심으로 서술하세요."
    )
    return "\n".join(lines)
