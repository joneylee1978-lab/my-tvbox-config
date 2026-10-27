#!/usr/bin/env python3
"""Candidate source monitoring only. Does not edit the TVBox player configuration."""
import datetime as dt
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CANDIDATES = ROOT / "candidate_sources.json"
REPORT = ROOT / "candidate_health.md"
PLAYBACK = ROOT / "playback_results.json"

PLAYBACK_STATUS = {
    "pass": "已實測通過",
    "previously_playable": "過去可播放",
    "partial": "部分可播放",
    "crash": "閃退／排除",
    "playback_failed": "播放失敗／排除",
    "not_tested": "尚未實測",
}
BLOCKED = {"crash", "playback_failed"}
TIMEOUT = 12
KEYWORDS = ["流浪地球", "航海王"]


def request_api(base, parameters):
    query = urllib.parse.urlencode(parameters)
    separator = "&" if "?" in base else "?"
    request = urllib.request.Request(
        base + separator + query,
        headers={"User-Agent": "Mozilla/5.0 TVBoxCandidateMonitor/1.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(500_000)
        return json.loads(raw.decode("utf-8-sig")), None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError,
            json.JSONDecodeError, UnicodeError, ValueError) as exc:
        return None, f"{type(exc).__name__}: {str(exc)[:100]}"


def grade(payload, error):
    if error:
        return "異常", error
    if not isinstance(payload, dict):
        return "異常", "不是 JSON 物件"
    if payload.get("code") not in (1, "1"):
        return "異常", f"code={payload.get('code')}，msg={payload.get('msg', '')}"
    entries = payload.get("list")
    if not isinstance(entries, list):
        return "不確定", "缺少 list 陣列"
    if not entries:
        return "無結果", "list 為空"
    return "正常", f"本頁 {len(entries)} 筆，total={payload.get('total', '未知')}"


def md_escape(s):
    return str(s).replace("|", "¦").replace("\n", " ").replace("\r", " ")[:140]


def main():
    data = json.loads(CANDIDATES.read_text(encoding="utf-8-sig"))
    playback = json.loads(PLAYBACK.read_text(encoding="utf-8-sig")) if PLAYBACK.exists() else {}
    actual = playback.get("sources", {})
    lines = [
        "# TVBox 候選片源檢測報告", "",
        "檢測時間：" + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "",
        "> 僅測 CMS API 列表和關鍵字搜尋；不代表 TVBox for Windows 播放相容、影片可播放或內容授權。",
        "> 不會修改 tvbox_windows_http_only.json，也不會自動加入或刪除來源。", "",
        "| 候選來源 | 片庫 API | 流浪地球 | 航海王 | TVBox 實測 | 推薦狀態 | 備註 |",
        "|---|---|---|---|---|---|---|",
    ]
    for source in data.get("sites", []):
        name = source.get("name", source.get("key", "未命名"))
        api = source.get("api", "")
        result = actual.get(source.get("key"), {})
        manual = result.get("status", "not_tested")
        manual_text = PLAYBACK_STATUS.get(manual, "紀錄值未知")
        manual_note = result.get("note", "")
        if source.get("type") != 1 or not api.startswith("https://"):
            lines.append(f"| {md_escape(name)} | 略過 | 略過 | 略過 | {manual_text} | 不推薦 | 非 HTTPS type=1 來源 |")
            continue
        statuses = []
        details = []
        for params in ({"ac": "list"}, *({"ac": "videolist", "wd": k} for k in KEYWORDS)):
            status, detail = grade(*request_api(api, params))
            statuses.append(status)
            details.append(detail)
        if manual in BLOCKED:
            recommendation = "不推薦（實測失敗）"
        elif manual == "pass" and all(s == "正常" for s in statuses):
            recommendation = "已通過（可保留）"
        elif manual == "pass":
            recommendation = "曾通過播放；API 須複查"
        else:
            recommendation = "待人工播放驗證"
        lines.append("| " + " | ".join(md_escape(x) for x in [name, *statuses, manual_text, recommendation, "；".join(details) + ("；人工實測：" + manual_note if manual_note else "")]) + " |")
    lines.extend(["", "推薦規則：人工實測『閃退』或『播放失敗』者，即使 API 全部正常，也一律標記為不推薦；人工通過且 API 正常才顯示已通過。", "此報告不會修改正式 TVBox JSON；人工實測結果需要手動更新 playback_results.json。", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.name} for {len(data.get('sites', []))} candidates")


if __name__ == "__main__":
    main()
