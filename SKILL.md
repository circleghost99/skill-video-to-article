---
name: video-to-article
description: |
  把單支影片（YouTube URL 或本地檔案）轉成結構化解讀型文章，自動提取關鍵投影片截圖與動態 GIF。
  當使用者說「把這影片整理成文章」「分析這支影片」「擷取簡報截圖」「影片轉文章」時觸發。
  不適用於：短摘要、逐字稿、純翻譯、多影片整合。
metadata:
  hermes:
    config:
      - key: gemini.api_key_env
        description: Gemini API Key 的環境變數名稱
        default: "GEMINI_API_KEY"
        prompt: Gemini API Key env var name
---

# Video to Article

把單支影片透過 **Gemini 視覺分析 → 智慧截圖 → 結構化文章** 的完整管線。

---

## 觸發條件

| 關鍵詞 | 動作 |
|--------|------|
| 「影片轉文章」「整理成文章」「寫成解讀文」 | 執行完整流程（Step 01–07） |
| 「分析這支影片」「擷取簡報截圖」 | 僅執行視覺分析（Step 01–02） |
| 「只要短摘要 / TL;DR」「只要逐字稿」 | **拒絕** — 非本 skill 核心價值 |

---

## 執行模式

| 選項 | 說明 |
|------|------|
| ✅ 自動執行 | 觸發後按步驟順序執行，Step 06 強制停等使用者回覆 |

---

## 執行規範（必須遵守）

1. **先讀後做**：執行 Step N 前，先讀對應的 reference 文件
2. **逐步驗證**：每步完成後檢查輸出是否符合預期
3. **不跳步驟**：必須按 01→02→...→07 順序執行

---

## 工作流（7 步）

| Step | 職責 | 執行者 | 參考文件 | 輸入 | 輸出 |
|------|------|--------|---------|------|------|
| 01 | 環境初始化 | 腳本 | — | 使用者觸發 | `{temp_dir}/` |
| 02 | Gemini 視覺分析 | 腳本 | — | 影片來源 | `analysis.json` |
| 03 | 素材擷取 | 腳本 | — | analysis.json + 影片 | `images/` + `manifest.json` |
| 04 | 字幕獲取清理 | 主Agent | `references/workflow-technical.md`, `references/fallbacks.md` | 影片 URL | `transcript_clean.txt` |
| 05 | 主題地圖萃取 | 主Agent | — | 字幕 + analysis.json | `notes_theme-map.md` |
| 06 | 草稿撰寫 | 主Agent | `references/output-format.md` | 主題地圖 + manifest | `article_draft.md` |
| 07 | Review + 交付 | 主Agent | `references/deployment-cleanup.md` | 草稿 + 素材 | 最終文章 |

---

## 各步驟詳細說明

### Step 01: 環境初始化

```bash
bash ${HERMES_SKILL_DIR}/scripts/prepare_temp_dir.sh
```

建立本次 session 專屬暫存目錄，後續所有中繼檔案存於此。

### Step 02: Gemini 視覺分析

使用 `video_analyzer.py` 透過 Gemini File API 分析影片，找出所有關鍵畫面。

```bash
python3 ${HERMES_SKILL_DIR}/scripts/video_analyzer.py "<影片來源>" \
  -o analysis.json \
  --strip-audio
```

| 參數 | 說明 |
|------|------|
| `<影片來源>` | 本地路徑或 YouTube URL |
| `--strip-audio` | **強烈建議**：去除音軌，防止模型被語音干擾視覺判斷 |
| `--keep-file` | 不刪除 Gemini 上的檔案，回傳 `file_uri` 供追問 |
| `--model` | 預設 `gemini-2.5-flash` |
| `--resolution` | `LOW`（預設）或 `HIGH` |
| `--extra-prompt` | 額外分析指示（如「注意 UI 操作」） |

**分析提示詞核心規則：**
1. ❌ 絕對禁止純人物畫面（Talking Head）
2. ✅ 只擷取完成畫面（動畫展開後的最終狀態）
3. ✅ 寧多勿少 — 每張不同投影片都要抓
4. ✅ GIF 嚴格標準 — 只有動態才有意義的片段

**輸出 JSON 結構：**

```json
{
  "success": true,
  "analysis": {
    "video_info": { "duration_seconds": 1278, "content_type": "mixed" },
    "key_frames": [
      { "timestamp": "MM:SS", "type": "screenshot",
        "importance": "high|medium",
        "description": "...", "article_context": "..." }
    ],
    "gif_segments": [
      { "start_time": "MM:SS", "end_time": "MM:SS",
        "description": "...", "article_context": "..." }
    ],
    "content_summary": "..."
  },
  "metadata": {
    "tokens": { "input_tokens": 124740, "estimated_cost_usd": 0.019 }
  }
}
```

**動態 FPS：** ≤1 小時 → 1.0 fps ｜ >1 小時 → 0.5 fps

### Step 03: 素材擷取

```bash
bash ${HERMES_SKILL_DIR}/scripts/extract_assets.sh \
  "<影片路徑>" analysis.json [output_dir]
```

**Smart Probe 機制：**
- 每個時間戳在 ±2 秒範圍取 5 張候選幀
- 自動選 JPEG 檔案最大的（= 視覺資訊最豐富 = 投影片而非暗色講者畫面）

**輸出：**
- `images/frame_NN_MM_SS.jpg` — 關鍵截圖
- `images/gif_NN_MM_SS-MM_SS.gif` — 動態片段（≤15 秒）
- `manifest.json` — 整合索引

### Step 04: 字幕獲取與清理

> **執行前必讀**：`references/workflow-technical.md` + `references/fallbacks.md`

- 優先用 `youtube-transcript-api` 或 `yt-dlp` 下載字幕
- 去除時間碼，合併破碎短句 → `transcript_clean.txt`
- 無可用字幕時依 fallbacks 規範處理

### Step 05: 主題地圖萃取

- **不要邊看字幕邊寫稿**
- 結合字幕 + `analysis.json` 的 `content_summary` 和各 `article_context`
- 抽離：問題背景 → 核心主張 → 轉化機制 → 關鍵案例 → 限制
- 產出 `notes_theme-map.md`

### Step 06: 草稿撰寫

> **執行前必讀**：`references/output-format.md`

- 將主題地圖擴寫為 Markdown 解讀文
- 在對應段落嵌入 `manifest.json` 中的截圖/GIF
- 遵循 Article-Grade 要求：拒絕過度壓縮
- 產出 `article_draft.md`

### Step 07: Review + 交付（🛑 強制中斷點）

> **執行前必讀**：`references/deployment-cleanup.md`

**⚠️ 先自我校對，再提交使用者：**

1. **原文/字幕比對**（必做）：
   - 重新讀取 `transcript_clean.txt` 或原始來源
   - 逐段確認文章沒有遺漏原文重要論點、數據、案例
   - 確認術語翻譯一致性（同一專有名詞不能一下中文一下英文）
   - 確認無英文殘留混雜（技術名詞除外）
2. **格式品質閘門**（必做）：
   - `grep -o '<[^>]*>' article_draft.md` 確認無 HTML tag 殘留
   - `grep -a $'\xe2\x80\x94' article_draft.md` 確認無 em dash 殘留
   - 確認符合 `references/output-format.md` §10 格式禁止項
3. 將校對後的 `article_draft.md` 與素材清單提交給使用者
4. **在此停下，等待使用者回覆**
5. 根據反饋修正
6. 依使用者指示發布
7. 完成後執行 `bash ${HERMES_SKILL_DIR}/scripts/cleanup_temp_dirs.sh`

---

## 環境需求

| 類型 | 需求 |
|------|------|
| 系統工具 | `yt-dlp`, `ffmpeg`, `ffprobe` |
| Python | `python3` + `google-genai` |
| 環境變數 | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` |
