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

> ⚠️ **嚴禁自行發揮替代流程**。每一步的腳本和工具都經過驗證，自行替代會導致路徑錯誤和產出品質問題。

1. **先讀後做**：執行 Step N 前，先讀對應的 reference 文件
2. **逐步驗證**：每步完成後檢查輸出是否符合預期
3. **不跳步驟**：必須按 01→02→...→07 順序執行，禁止跳步
4. **路徑規則**：`${HERMES_SKILL_DIR}` 已由 Hermes 自動展開為本 Skill 的絕對路徑。直接複製貼上指令即可，**絕對不要自行推測或硬編碼路徑**
5. **配圖定位**：本 Skill 的配圖 = **影片原始截圖**（透過 Gemini 分析 + ffmpeg 擷取）。Step 02 和 Step 03 是**預設必做**，不需要使用者明確要求。如果使用者額外需要 AI 生成的插圖，會另外指定使用 `baoyu-article-illustrator` 等生圖 Skill，**v2a 本身不負責 AI 生圖**

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

> 直接執行以下指令（`${HERMES_SKILL_DIR}` 已自動展開，不需修改）：

```bash
bash ${HERMES_SKILL_DIR}/scripts/prepare_temp_dir.sh
```

建立本次 session 專屬暫存目錄，後續所有中繼檔案存於此。

### Step 02: Gemini 視覺分析（預設必做）

> ⚠️ **本步驟為預設行為，一律執行**。影片截圖是 v2a 的核心產出之一，不是可選項。

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

> 直接執行以下指令（`${HERMES_SKILL_DIR}` 已自動展開，不需修改）：

```bash
bash ${HERMES_SKILL_DIR}/scripts/extract_assets.sh \
  "<影片路徑>" analysis.json [output_dir]
```

**直接時間戳擷取：** 使用 Gemini 回傳的精確時間戳，直接擷取該時刻的幀。Gemini 已經看過影片，不需要額外的啟發式選幀。

**輸出：**
- `images/frame_NN_MM_SS.jpg` — 關鍵截圖
- `images/gif_NN_MM_SS-MM_SS.gif` — 動態片段（≤12 秒）
- `manifest.json` — 整合索引

**封面圖：** `analysis.json` 包含 `cover_frame` 欄位（時間戳＋原因），用於後續 Notion 發布時的封面圖選擇。

**品質檢查（必做，不可跳過）：**

素材擷取完成後，執行以下檢查流程：

1. **Contact sheet 快篩**：用 `vision_analyze` 看 contact sheet，快速發現明顯問題
2. **逐張深檢**：對所有 `importance: high` 的 key_frame，**逐張** `vision_analyze` 確認：
   - 文字是否清晰可讀？（不是動態模糊/過渡動畫中間態）
   - 投影片/UI 內容是否完整展開？（不是半顯示狀態）
   - 有沒有講者遮擋主要內容？
3. **修復流程**：發現問題幀時，用 ffmpeg 在 ±1~2 秒範圍嘗試多個時間點，再次 `vision_analyze` 選最清晰的替換

⚠️ 「只看 contact sheet」不夠！縮圖太小看不出文字模糊，必須逐張檢查 high importance 幀。

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

### Step 06: 草稿撰寫（純文字）

> **執行前必讀**：`references/output-format.md`

- 文章開頭**必須包含 YAML frontmatter**（§8 定義的所有必填欄位）
- 文章本文從 H2 開始，**不要寫 H1 標題**（Notion Name 屬性已是標題）
- 將主題地圖擴寫為 Markdown 解讀文
- ⚠️ **此步驟先不嵌入圖片**，專注在文字內容的品質和完整度
- 遵循 Article-Grade 要求：拒絕過度壓縮
- 產出 `article_draft.md`（純文字版）

### Step 07: Review + 配圖 + 交付（🛑 強制中斷點）

> **執行前必讀**：`references/deployment-cleanup.md`

**⚠️ 三階段校對，依序執行：**

**Phase 1：內容校對 — 回頭 review 字幕補漏**
1. 重新讀取 `transcript_clean.txt` 或原始來源
2. 逐段比對文章與原文，找出遺漏的：
   - 重要論點、數據、具體案例
   - 關鍵的轉化邏輯（A→B→C 不能跳步）
   - 邊界條件、使用限制
3. 將遺漏的內容**補回文章對應段落**（不是列清單，是融入文章）
4. 確認術語翻譯一致性（同一專有名詞不能一下中文一下英文）
5. 確認無英文殘留混雜（技術名詞除外）

**Phase 2：配圖 — 嵌入截圖/GIF（使用本地路徑）**
1. 讀取 `manifest.json`，依時間順序將截圖/GIF 嵌入文章對應段落
2. 按 manifest 去重結果嵌入，不重複放（同一內容只有 frame 或 GIF）
3. 每張圖的 alt text 要有描述性（不要寫「圖片」）
4. **圖片路徑直接用本地絕對路徑**（如 `/var/folders/.../images/frame_01.jpg`）
   - `notion_hamster_push.py` 會自動上傳到 Cloudinary 並替換為 CDN URL
   - ⚠️ 不需要手動上傳 Cloudinary！
5. ❌ **禁止連續圖片**：兩張圖/GIF 之間必須有至少一段文字說明，不可紧接插入
   - 如果兩張圖屬於同一段落，只保留最有代表性的一張
   - 如果兩張圖都必要，在中間插入轉場文字解說它們的差異

**Phase 3：格式品質閘門**
1. `grep -o '<[^>]*>' article_draft.md` 確認無 HTML tag 殘留
2. `grep -a $'\xe2\x80\x94' article_draft.md` 確認無 em dash 殘留
3. 確認符合 `references/output-format.md` §10 格式禁止項

**交付：**
1. 將校對後的 `article_draft.md` 與素材清單提交給使用者
2. **在此停下，等待使用者回覆**
3. 根據反饋修正
4. 依使用者指示發布：
   ```bash
   # ✅ 只需兩個參數！frontmatter 中的 tags/url/note/cover 會自動讀取
   # ❌ 不要再手動傳 --tags --url --note --image，那些已在 frontmatter 裡
   python3 ~/.hermes/skills/openclaw-imports/circleghost-content-hamster-reporting/scripts/python/notion_hamster_push.py \
     --title "文章標題" --file article_draft.md
   ```
   推送成功後會自動生成 `notion_manifest.json`（image→block_id 映射）。

   **修復圖片/更新文章**：如果發現模糊圖片或需要修改文章，**不要手寫 Notion API**！用 `--update` 模式重新推送整篇文章：
   ```bash
   python3 ~/.hermes/skills/openclaw-imports/circleghost-content-hamster-reporting/scripts/python/notion_hamster_push.py \
     --title "文章標題" --file article_draft.md --update <PAGE_ID>
   ```
   這會清除舊 blocks → 重新上傳，自動處理 Cloudinary 和圖片替換。

5. 複製到 Obsidian：`cp article_draft.md ~/Desktop/同步知識庫/30_Projects/倉鼠特報/發佈區/`
6. 完成後執行 `bash ${HERMES_SKILL_DIR}/scripts/cleanup_temp_dirs.sh`

> ⚠️ **注意**：`/var/folders/` 等 temp 路徑會被 `write_file` 工具拒絕。
> 寫入文章時請用 `terminal` 工具（如 `cat > article_draft.md << 'EOF'`）。

---

## 環境需求

| 類型 | 需求 |
|------|------|
| 系統工具 | `yt-dlp`, `ffmpeg`, `ffprobe` |
| Python | `python3` + `google-genai` |
| 環境變數 | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` |
