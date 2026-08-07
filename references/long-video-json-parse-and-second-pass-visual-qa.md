# 長影片 JSON 解析失敗與 accepted-only 二次視覺 QA

## 適用情境

Gemini 已成功處理並分析長影片，HTTP 與 token 計費均正常，但 `video_analyzer.py` 在 parse 階段失敗；或視覺子代理已標示 accepted，主 Agent contact-sheet 覆核仍發現控制圖示、游標、動畫未展開或近重複幀。

## 1. 成功推理但 JSON 無效

典型案例：模型把整數欄位寫成未加引號的時間格式：

```json
"duration_seconds": 104:28
```

這代表輸出格式失敗，不代表影片上傳、Gemini provider 或視覺推理失敗。處理方式：

1. 保留已下載的原始高解析影片，不重新下載。
2. 超過約 60 分鐘時切成 60 分鐘左右的無音訊段落。
3. 每段 prompt 明確規定：`duration_seconds` 必須是純整數秒數，禁止 `MM:SS`；`timestamp` 才使用 `MM:SS`。
4. 平行分析各段，成功後把後段 timestamp 加回 offset。
5. 合併資料時保留 `source_part` 與 `timestamp_seconds`，最終截圖仍從原始高解析影片擷取。
6. 回報時寫「Gemini 推理成功，但 JSON parse 失敗，已分段恢復」，不要誤報成 provider 故障。

## 2. `extract_assets.sh` 第一幀即退出

若 log 只停在 `[1/N] timestamp — description`，依既有 manual ffmpeg fallback：按合併後 `timestamp_seconds` 從原始影片直接抽幀，建立相容 `manifest.json`。這次 long-video 實測證明，58 張 frame 可機械批次抽取；後續品質仍須由 vision gate 決定，不能因抽取成功就全部入稿。

## 3. accepted-only 二次視覺 QA

子代理 QA 的 accepted 並非最終結論。主 Agent必須再看 accepted-only contact sheets，並有權覆寫 accepted 狀態。特別掃：

- 左下角播放器／投影片控制圖示
- 游標殘留
- 文字密集嵌圖模糊
- 動畫尚未完整展開或圖層互相遮擋
- 同頁早期動畫與完整版本近重複
- 密集時間戳聲稱一秒內切換多張不同投影片

若 vision request 暫時失敗，只重試該 contact sheet，不重跑整批。最終 manifest 只保留主 Agent 視覺通過的 assets；rejected 檔案移入保留目錄，不永久刪除。

## 4. Contact sheet 上限

`create_contact_sheet.py` 一次最多使用 4 張圖，傳入更多只會取前 4 張並印 warning。建立 QA 聯絡單時嚴格每批不超過 4 張；不要用「12 張一批」卻誤以為全部已被檢查。

## 5. Shell backtick 坑

用 `python3 -c "..."` 寫含 Markdown backticks 的中文段落時，shell 會把反引號當 command substitution，造成內容被吃掉甚至執行意外命令。長文或含 backticks 的寫回一律用 quoted heredoc：

```bash
python3 <<'PY'
from pathlib import Path
# 內容中的 `backticks` 不會被 shell 展開
PY
```

寫回後立刻讀取受影響段落，不能只看 exit code 0。
