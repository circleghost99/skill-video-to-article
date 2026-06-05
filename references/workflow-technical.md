# Technical Workflow Reference

這份文件定義 `video-to-article` v1 的技術主流程。

## v1 技術定位

v1 先支援：
- **單支 YouTube**
- **字幕優先**（YT 字幕為主來源）
- **無字幕時退到本地 ASR（mlx-whisper large-v3）**
- **字幕驅動的文章化流程**

不要把這份流程當成多平台、多影片 pipeline。

## 1. 暫存目錄

每次執行都建立專屬暫存目錄，避免覆蓋與污染工作區。

- 初始化：`scripts/prepare_temp_dir.sh`
- 建議路徑：`$WORKSPACE/.tmp/v2a/<session_id>`

建議檔案佈局：

```text
.tmp/v2a/<session_id>/
├── metadata.txt
├── transcript_raw.vtt
├── transcript_clean.txt
├── notes_theme-map.md
├── frames/
│   ├── explore/
│   └── final/
└── article_draft.md
```

## 2. YouTube 字幕取得順序

### Step 1 — 確認基本資料
先確認：
- title
- channel
- duration
- available subtitles / captions

可用 `yt-dlp --list-subs <url>` 檢查。

### Step 2 — 優先順序
字幕優先順序：
1. **人工字幕（原語）**
2. **人工字幕（可接受語言版本）**
3. **YouTube automatic captions**

若只有 auto captions，不代表不能做；但要先做清理再進文章流程。

### Step 3 — 下載與保存

**首選做法：呼叫 `scripts/get_transcript.py`** ⭐

這支腳本固化了完整的優先鏈，**禁止 agent 自己重寫 Python 抓字幕邏輯**（過去多次因 API 不熟悉、錯誤訊息誤判而走鐘）。

```bash
/Users/circleghost/.hermes/hermes-agent/venv/bin/python3 \
  /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/get_transcript.py \
  --url "$URL" \
  --out-dir "$WORK" \
  --audio "$WORK/audio.wav" \
  --lang zh
```

腳本內部優先順序（YT 字幕為主，本地 ASR 為輔）：
1. **`youtube-transcript-api`** — 先抓人工字幕，無則退到 auto-caption
2. **`yt-dlp --write-subs --write-auto-subs`** — 第一次只抓人工，沒有再抓 auto；含 429 退避（5s, 15s）
3. **`mlx-whisper large-v3` 本地轉錄** — 僅當 1+2 都拿不到任何字幕時才啟動，需傳 `--audio`

**腳本輸出：**
- `transcript_raw.json` — 段落時間軸 `[{start, duration, text}, ...]`
- `transcript_clean.txt` — 已清理、依 30 秒切塊、含 `[MM:SS]` 標記
- stdout: JSON 狀態報告

**狀態報告範例（成功）：**
```json
{
  "ok": true,
  "method": "youtube-transcript-api",
  "language": "zh-TW",
  "is_generated": false,
  "segments": 2307,
  "duration_sec": 7157.76,
  "raw_path": "/path/to/transcript_raw.json",
  "clean_path": "/path/to/transcript_clean.txt",
  "quality_badge": "🟢 人工字幕"
}
```

`quality_badge` **必須寫進文章 frontmatter** 給讀者透明度（特別是 fallback 到 whisper 時）。

**flag 行為：**
- `--skip-whisper`：完全禁用 ASR fallback（僅當你明確要求字幕版本，不接受 ASR 結果時用）
- `--lang en`：英文影片改用此 flag

**錯誤處理：**
- exit code 2：URL 解析失敗
- exit code 3：YT 無字幕且未提供 `--audio`（或設了 `--skip-whisper`）
- exit code 4：所有方法都失敗

收到 exit 3 時，agent 應決定：a) 提示使用者影片無字幕並請求是否啟用 ASR，b) 重跑時補上 `--audio` 路徑。

---

**底層 API 用法（除錯用，平時用腳本就好）**

只有在腳本本身需要修改、或需獨立呼叫某一層時才參考以下範例。

`youtube-transcript-api`（v1.x 正確用法）：
```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
transcript_list = api.list(video_id='VIDEO_ID')  # ⚠️ 不是 fetch()
for t in transcript_list:
    print(t.language_code, t.is_generated)
chosen = sorted(transcript_list, key=lambda t: (t.is_generated, t.language_code != 'zh-TW'))[0]
fetched = chosen.fetch()  # iterable of FetchedTranscriptSnippet (text, start, duration)
```

⚠️ **常見錯誤**：把 `YouTubeTranscriptApi.fetch(...)` 當 class method 呼叫會失敗。**必須先 `api = YouTubeTranscriptApi()` instance 再 `api.list()`**。

`yt-dlp` 字幕語言代碼可能很怪（`zh-Hans-zh` = 簡體 from 中文 auto-caption）。先 `yt-dlp --list-subs "$URL"` 看清楚再決定 `--sub-langs`。

**429 Too Many Requests：** 詳見 `references/fallbacks.md`。腳本已內建 5s/15s 退避重試。

## 3. 分析順序

### 不要直接寫稿
看到字幕後，先抽這幾層：
- 影片要解決什麼問題
- 作者的核心主張是什麼
- 影片怎麼分段推進
- 哪些例子只是輔助，哪些才是骨幹
- 最值得保留的 3-5 個洞察

### 再做主題地圖
把整理結果寫到：
- `notes_theme-map.md`

最少要有：
- 核心命題
- 次命題
- 重要術語
- 支撐例子
- 文章適合的 H2 結構

## 4. 文章生成節奏

v1 預設是 **transcript-first, synthesis-first**：

1. 取得字幕
2. 清理字幕
3. 建立主題地圖
4. 產出文章骨架
5. 補足段落與洞察
6. 最後才考慮視覺素材

若是概念解說型影片，視覺可以是 optional。

## 5. 視覺素材判斷

只有在以下情況才值得做畫面提取：
- 畫面有流程圖 / 架構圖 / UI 對照
- 講者明確依賴畫面說明概念
- 沒截圖會少一層理解

若影片主要靠口語講解，先不要啟動重畫面流程。

## 6. v1 停損點

以下情況，不要硬進完整文章流程：
- 字幕與本地 ASR **都失敗**（腳本回 exit 4 或 ASR 產出 0 segments）
- ASR 噪音高到無法判讀主張（`quality_badge` 是 🟡 ASR 且文章潤稿時發現大量無法理解段落）
- 影片本身資訊密度過低

⚠️ 「沒有 YT 字幕」**不再**自動觸發停損 — 腳本會降級到 mlx-whisper。但若 `quality_badge` 是 🟡 ASR，frontmatter **必須**標註，且文章開頭請補一行：「本文逐字稿由本地 ASR 轉錄，可能有人名/術語誤辨」。

遇到真停損情況，交給 `references/fallbacks.md` 決定是降級還是停下。
