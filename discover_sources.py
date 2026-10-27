#!/usr/bin/env python3
"""Produce a review-only discovery report; never modify deployed TVBox configurations."""
import datetime as dt
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEEDS = ROOT / "discovery_feeds.json"
CANDIDATES = ROOT / "candidate_sources.json"
OFFICIAL = ROOT / "tvbox_windows_http_only.json"
PLAYBACK = ROOT / "playback_results.json"
REPORT = ROOT / "discovery_report.md"


def read_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return fallback


def norm_api(value):
    try:
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return None
        if parsed.port not in (None, 443) or parsed.query or parsed.fragment:
            return None
        host = parsed.hostname.lower()
        if host in {"localhost", "127.0.0.1", "::1"} or host.endswith((".local", ".internal")):
            return None
        if not re.fullmatch(r"[a-z0-9.-]+", host) or "." not in host:
            return None
        path = parsed.path.rstrip("/")
        if not path or not ("api.php" in path or "provide/vod" in path):
            return None
        return urllib.parse.urlunsplit(("https", host, path, "", ""))
    except (ValueError, TypeError, AttributeError):
        return None


def fetch_feed(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in {"raw.githubusercontent.com"}:
        raise ValueError("Feed must be a reviewed raw.githubusercontent.com HTTPS URL")
    request = urllib.request.Request(url, headers={"User-Agent": "TVBoxDiscovery/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=15) as response:
        data = response.read(2_000_001)
    if len(data) > 2_000_000:
        raise ValueError("Feed exceeds size limit")
    return json.loads(data.decode("utf-8-sig"))


def escape(value):
    return str(value).replace("|", "¦").replace("\n", " ").replace("\r", " ")[:120]


def main():
    settings = read_json(FEEDS, {"feeds": [], "max_new_candidates": 25})
    existing = read_json(CANDIDATES, {}).get("sites", []) + read_json(OFFICIAL, {}).get("sites", [])
    tested = read_json(PLAYBACK, {}).get("sources", {})
    known_keys = {str(s.get("key", "")) for s in existing} | set(tested)
    known_apis = {api for s in existing if (api := norm_api(s.get("api", "")))}
    cap = max(1, min(50, int(settings.get("max_new_candidates", 25))))
    found = []
    problems = []
    total_seen = 0
    for feed in settings.get("feeds", []):
        if not feed.get("enabled"):
            continue
        try:
            payload = fetch_feed(feed["url"])
            if not isinstance(payload, dict) or not isinstance(payload.get("sites"), list):
                raise ValueError("No sites array in feed")
            for src in payload["sites"]:
                if not isinstance(src, dict) or src.get("type") != 1:
                    continue
                api = norm_api(src.get("api", ""))
                if not api:
                    continue
                total_seen += 1
                key = str(src.get("key", ""))
                if key in known_keys or api in known_apis:
                    continue
                name = str(src.get("name", "Unnamed"))
                known_keys.add(key)
                known_apis.add(api)
                found.append((name, api, feed.get("name", "Feed")))
                if len(found) >= cap:
                    break
        except (ValueError, KeyError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            problems.append((feed.get("name", "Feed"), f"{type(exc).__name__}: {str(exc)[:110]}"))
        if len(found) >= cap:
            break
    lines = ["# TVBox 新來源候選清單（僅供人工審核）", "",
             "產生時間：" + dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), "",
             "> 僅擷取核准來源清單中 HTTPS、type=1、CMS 型態的候選；沒有驗證搜尋、播放、授權或安全性。",
             "> 不自動更改正式配置、候選池或播放實測紀錄；發現結果不等於推薦。", "",
             f"既有來源已排除；來源中符合初步格式條件的項目：{total_seen}；新候選：{len(found)}。", "",
             "| 名稱 | API | 來源清單 |", "|---|---|---|"]
    for name, api, feed in found:
        lines.append(f"| {escape(name)} | `{escape(api)}` | {escape(feed)} |")
    if not found:
        lines.append("| 尚無新候選 | — | — |")
    if problems:
        lines.extend(["", "## 讀取問題", ""])
        lines.extend(f"- {escape(name)}：{escape(issue)}" for name, issue in problems)
    lines += ["", "下一步：人工確認來源可信度與授權，挑選後加入 candidate_sources.json 進行 API 檢測，最後在 Windows TVBox 實測播放。", ""]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {REPORT.name}: {len(found)} new candidates, {len(problems)} feed errors")

if __name__ == "__main__":
    main()
