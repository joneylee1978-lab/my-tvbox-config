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
    lines = [
        "# TVBox 候選片源檢測報告", "",
        "檢測時間：" + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "",
        "> 僅測 CMS API 列表和關鍵字搜尋；不代表 TVBox for Windows 播放相容、影片可播放或內容授權。",
        "> 不會修改 tvbox_windows_http_only.json，也不會自動加入或刪除來源。", "",
        "| 候選來源 | 片庫 API | 流浪地球 | 航海王 | 備註 |",
        "|---|---|---|---|---|",
    ]
    for source in data.get("sites", []):
        name = source.get("name", source.get("key", "未命名"))
        api = source.get("api", "")
        if source.get("type") != 1 or not api.startswith("https://"):
            lines.append(f"| {md_escape(name)} | 略過 | 略過 | 略過 | 非 HTTPS type=1 來源 |")
            continue
        statuses = []
        details = []
        for params in ({"ac": "list"}, *({"ac": "videolist", "wd": k} for k in KEYWORDS)):
            status, detail = grade(*request_api(api, params))
            statuses.append(status)
            details.append(detail)
        lines.append("| " + " | ".join(md_escape(x) for x in [name, *statuses, "；".join(details)]) + " |")
    lines.extend(["", "建議：以連續多次結果判斷穩定性，且在 TVBox 實測播放前，不要自動納入正式配置。", ""])
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.name} for {len(data.get('sites', []))} candidates")


if __name__ == "__main__":
    main()
