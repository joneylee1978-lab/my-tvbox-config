# TVBox 候選片源檢測報告

檢測時間：2026-11-19 08:53 UTC

> 僅測 CMS API 列表和關鍵字搜尋；不代表 TVBox for Windows 播放相容、影片可播放或內容授權。
> 不會修改 tvbox_windows_http_only.json，也不會自動加入或刪除來源。

| 候選來源 | 片庫 API | 流浪地球 | 航海王 | TVBox 實測 | 推薦狀態 | 備註 |
|---|---|---|---|---|---|---|
| 最大資源 | 正常 | 異常 | 異常 | 已實測通過 | 曾通過播放；API 須複查 | 本頁 20 筆，total=126048；JSONDecodeError: Unterminated string starting at: line 1 column 488457 (char 488456)；JSONDecodeError: Unterminated stri |
| 極速資源 | 正常 | 正常 | 正常 | 閃退／排除 | 不推薦（實測失敗） | 本頁 20 筆，total=117025；本頁 5 筆，total=5；本頁 6 筆，total=6；人工實測：Two different titles crash TVBox.exe on play; coreclr.dll APPCRASH c0000005 in Windo |
| 新浪資源 | 正常 | 正常 | 正常 | 尚未實測 | 待人工播放驗證 | 本頁 20 筆，total=118723；本頁 5 筆，total=5；本頁 6 筆，total=6；人工實測：API reports uncertain; not tested in this TVBox PC |
| 360 資源 | 正常 | 正常 | 正常 | 播放失敗／排除 | 不推薦（實測失敗） | 本頁 20 筆，total=75341；本頁 3 筆，total=3；本頁 4 筆，total=4；人工實測：Search OK, multiple streams/titles fail with avformat_open_input End of file |
| 魔都資源 | 正常 | 正常 | 正常 | 已實測通過 | 已通過（可保留） | 本頁 20 筆，total=92045；本頁 4 筆，total=4；本頁 3 筆，total=3；人工實測：Search and playback tested OK |
| 速播資源 | 正常 | 正常 | 正常 | 閃退／排除 | 不推薦（實測失敗） | 本頁 20 筆，total=118618；本頁 5 筆，total=5；本頁 8 筆，total=8；人工實測：Playback crashes TVBox.exe |

推薦規則：人工實測『閃退』或『播放失敗』者，即使 API 全部正常，也一律標記為不推薦；人工通過且 API 正常才顯示已通過。
此報告不會修改正式 TVBox JSON；人工實測結果需要手動更新 playback_results.json。
