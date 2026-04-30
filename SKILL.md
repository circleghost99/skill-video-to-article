---
name: video-to-article
description: |
  把單支影片（YouTube URL 或本地檔案）透過 Gemini 視覺分析轉成結構化解讀型文章。
  自動提取所有關鍵投影片截圖與動態 GIF，產出 manifest.json 供後續文章撰寫。
  觸發時機：使用者要求分析影片、把影片內容重組成可閱讀的長文、深度筆記或 markdown 文章。
  不適用：短摘要、逐字稿、純翻譯、多影片整合。
metadata:
  requires:
    bins:
      - yt-dlp
      - ffmpeg
      - ffprobe
    python: ["python3"]
    pip: ["google-genai"]
    env: ["GEMINI_API_KEY"]
---

# Video to Article

專門處理：**單支影片 → Gemini 視覺分析 → 結構化素材 → 解讀型文章**。

## 觸發訊號 (Triggers)

| 使用者意圖 | 動作與判斷 |
|---|---|
| 「把這影片整理成文章 / 長文」 | **觸發主流程** |
| 「分析這支影片 / 擷取簡報截圖」 | **觸發 Gemini 分析管線** |
| 「寫成解讀文，不要只摘要」 | **觸發主流程** |
| 「只要短摘要 / TL;DR」 | 拒絕或降級（非本 skill 核心價值） |
| 「只要逐字稿」 | 拒絕或降級（非本 skill 核心價值） |

## 核心工具

### `scripts/video_analyzer.py` — Gemini 影片視覺分析

用 Gemini File API 上傳影片，以嚴格的視覺分析提示詞找出所有關鍵畫面，回傳結構化 JSON。

```bash
# 基本用法（本地檔案）
python3 scripts/video_analyzer.py video.mp4 -o analysis.json

# YouTube URL
python3 scripts/video_analyzer.py "https://www.youtube.com/watch?v=XXX" -o analysis.json

# 推薦用法：去除音訊，純視覺分析（避免音訊干擾判斷）
python3 scripts/video_analyzer.py video.mp4 -o analysis.json --strip-audio

# 保留上傳檔案供後續追問
python3 scripts/video_analyzer.py video.mp4 -o analysis.json --strip-audio --keep-file

# 附加指示
python3 scripts/video_analyzer.py video.mp4 -o analysis.json --extra-prompt "注意 UI 操作畫面"
```

**參數說明：**

| 參數 | 說明 |
|------|------|
| `source` | 影片路徑或 YouTube URL（必填） |
| `-o / --output` | 輸出 JSON 路徑 |
| `--strip-audio` | 去除音軌後再上傳（**強烈建議**：防止模型被語音內容影響視覺判斷） |
| `--keep-file` | 不刪除 Gemini File API 上的檔案，回傳 `file_uri` 供後續追問 |
| `--model` | 模型選擇（預設 `gemini-3-flash-preview`） |
| `--resolution` | `LOW`（預設）或 `HIGH` |
| `--extra-prompt` | 額外分析指示 |
| `-v / --verbose` | 顯示詳細日誌 |

**輸出 JSON 結構：**
```json
{
  "success": true,
  "analysis": {
    "video_info": { "duration_seconds": 1278, "content_type": "mixed", "title_inferred": "..." },
    "key_frames": [
      { "timestamp": "MM:SS", "type": "screenshot", "importance": "high|medium",
        "description": "...", "article_context": "..." }
    ],
    "gif_segments": [
      { "start_time": "MM:SS", "end_time": "MM:SS", "description": "...", "article_context": "..." }
    ],
    "content_summary": "..."
  },
  "metadata": {
    "model": "gemini-3-flash-preview",
    "tokens": { "input_tokens": 124740, "output_tokens": 1865, "estimated_cost_usd": 0.019 },
    "timing": { "upload_seconds": 16.1, "processing_seconds": 143.1, "analysis_seconds": 183.9 }
  }
}
```

**分析提示詞核心規則：**
1. **絕對禁止純人物畫面**（Talking Head）— 必須含可閱讀資訊
2. **只擷取完成畫面**（最終狀態）— 不要動畫進行中的中間態
3. **寧多勿少** — 每張不同的簡報都要抓
4. **GIF 嚴格標準** — 只有動態才有意義的片段

**動態 FPS：**
- ≤1 小時：1.0 fps
- \>1 小時：0.5 fps

### `scripts/extract_assets.sh` — 從影片擷取截圖與 GIF

根據 `video_analyzer.py` 產出的 JSON，用 ffmpeg 從影片擷取實際的圖片和 GIF。

```bash
scripts/extract_assets.sh <video_path> <analysis_json> [output_dir]
```

**Smart Probe 機制：**
- 每個時間戳會在 ±2 秒範圍內取 5 張候選幀
- 自動選擇 JPEG 檔案最大的那張（= 視覺資訊最豐富 = 投影片而非暗色講者畫面）
- 解決鏡頭切換導致的幀對齊問題

**輸出：**
- `output_dir/images/frame_01_MM_SS.jpg` — 關鍵截圖
- `output_dir/images/gif_01_MM_SS-MM_SS.gif` — 動態片段（自動限制 ≤15 秒）
- `output_dir/manifest.json` — 整合索引（含描述、重要性、文章用途）

## 參考檔案 (References)

執行對應步驟時必須讀取：
- 📂 `references/workflow-technical.md` — 下載字幕規則、處理 yt-dlp 429 錯誤
- 📂 `references/fallbacks.md` — 字幕品質判定與降級邊界
- 📂 `references/output-format.md` — 文章骨架 (Article-Grade)、段落與洞察寫法
- 📂 `references/visual-extraction.md` — 視覺 Pass 1/Pass 2 提取策略
- 📂 `references/deployment-cleanup.md` — Discord/Obsidian 交付規範

## 標準工作流 (Standard Workflow)

### Step 0: 初始化環境
- **強制執行**：呼叫 `scripts/prepare_temp_dir.sh` 建立本次 session 的專屬暫存目錄。

### Step 1: Gemini 視覺分析
- 使用 `scripts/video_analyzer.py` 分析影片。
- **建議加上 `--strip-audio`**，確保純視覺判斷。
- 檢查回傳的 `success` 欄位和 `metadata.tokens` 確認成本。

### Step 2: 素材擷取
- 使用 `scripts/extract_assets.sh` 從影片擷取截圖與 GIF。
- 檢查 `manifest.json` 確認所有素材已正確擷取。

### Step 3: 字幕獲取與清理 (Read: `workflow-technical.md`, `fallbacks.md`)
- 獲取影片字幕（`yt-dlp` 或 `youtube-transcript-api`）。
- 去除時間碼，合併破碎短句，產出 `transcript_clean.txt`。
- 若無可用字幕，依 fallbacks 規範停下或降級。

### Step 4: 主題地圖萃取 (Synthesis)
- 結合字幕內容與 Gemini 分析結果（`content_summary`、各 `article_context`）。
- 抽離：問題背景、核心主張、轉化機制、關鍵案例與限制。
- 產出 `notes_theme-map.md` 作為文章骨幹。

### Step 5: 草稿撰寫 (Read: `output-format.md`)
- 將主題地圖擴寫為具備厚度的 Markdown 解讀文。
- 在對應段落嵌入 `manifest.json` 中的截圖/GIF。
- 產出 `article_draft.md`。

### Step 6: Review Pass (強制中斷點)
- 將 `article_draft.md` 內容與素材清單提交給使用者。
- **在此停下，等待使用者回覆。**

### Step 7: 交付與清理 (Read: `deployment-cleanup.md`)
- 依使用者指示發布。
- 確認交付成功後，執行 `scripts/cleanup_temp_dirs.sh`。
