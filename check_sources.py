#!/usr/bin/env python3
"""Read TVBox config and generate a non-destructive API health report."""
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'tvbox_windows_http_only.json'
REPORT = ROOT / 'source_health.md'
KEYWORD = '流浪地球'
TIMEOUT = 12


def get_json(base, params):
    url = base + ('&' if '?' in base else '?') + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 TVBoxSourceMonitor/1.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as r:
            raw = r.read(512_000)
            if r.status != 200:
                return None, f'HTTP {r.status}'
            return json.loads(raw.decode('utf-8-sig')), None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeError, ValueError) as e:
        return None, f'{type(e).__name__}: {str(e)[:100]}'


def assess(payload):
    if not isinstance(payload, dict):
        return '異常', '回應不是 JSON 物件'
    code = payload.get('code')
    if code not in (1, '1'):
        return '異常', f'API code={code}; msg={str(payload.get("msg", ""))[:80]}'
    entries = payload.get('list')
    if not isinstance(entries, list):
        return '不確定', '未回傳標準 list 陣列'
    return ('正常' if entries else '不確定'), f'回傳 {len(entries)} 筆（total={payload.get("total", "未知")}）'


def escape(value):
    return str(value).replace('|', '¦').replace('\n', ' ')[:180]


def main():
    config = json.loads(CONFIG.read_text(encoding='utf-8-sig'))
    rows = []
    for source in config.get('sites', []):
        name = source.get('name', source.get('key', '未命名'))
        api = source.get('api', '')
        if source.get('type') != 1 or not api.startswith('https://'):
            rows.append((name, '略過', '略過', '非 HTTPS type=1 來源'))
            continue
        inventory, inventory_error = get_json(api, {'ac': 'list'})
        keyword, keyword_error = get_json(api, {'ac': 'videolist', 'wd': KEYWORD})
        inventory_status, inventory_note = ('異常', inventory_error) if inventory_error else assess(inventory)
        search_status, search_note = ('異常', keyword_error) if keyword_error else assess(keyword)
        rows.append((name, inventory_status, search_status, f'片庫：{inventory_note}；搜尋：{search_note}'))

    now = dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    content = [
        '# TVBox 片源健康檢測', '', f'檢測時間：{now}',
        f'關鍵字測試：{KEYWORD}', '',
        '> 僅檢查 CMS API 回應，不會驗證影片能否播放、版權授權或播放器相容性。',
        '> 本工具不會更改、停用或刪除原本 JSON 的任何片源。', '',
        '| 來源 | 片庫列表 | 關鍵字搜尋 | 說明 |',
        '|---|---|---|---|',
    ]
    content.extend(f'| {escape(name)} | {escape(inv)} | {escape(search)} | {escape(note)} |' for name, inv, search, note in rows)
    content.extend(['', '注意：短暫失敗可能是連線或網站限制，請結合多天報告與人工播放測試判斷。', ''])
    REPORT.write_text('\n'.join(content), encoding='utf-8')
    print(REPORT.read_text(encoding='utf-8'))

if __name__ == '__main__':
    main()
