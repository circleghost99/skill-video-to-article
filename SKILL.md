---
name: video-to-article
description: |
  影片深度解讀 pipeline。從 YouTube 影片或本地影片檔，透過 Gemini 視覺分析、字幕萃取、主題地圖建構、深度解讀寫作，產出圖文並茂的分析文章並推送至 Notion。
  當使用者說「解讀這個影片」「把這影片整理成文章」「用倉鼠寫文 skill」「分析這支影片」「擷取簡報截圖」「影片轉文章」「v2a」時觸發。
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

影片深度解讀 pipeline：**Gemini 視覺分析 → 智慧截圖 → 主題萃取 → 解讀寫作**，產出圖文並茂的分析文章。

---

## 適用範圍

本 Skill 是倉鼠特報員的**影片解讀 pipeline**，包含視覺分析 + 深度寫作。

| 使用者說 | 用哪個 Skill |
|----------|-------------|
| 「解讀這個影片」「寫文」「v2a」「影片轉文章」 | ✅ video-to-article |
| 「分析這篇文章的寫作技巧」「學習創作手法」 | ❌ 用 `hamster-writing-craft` |
| 「執行倉鼠特報」「特報」 | ❌ 用 `circleghost-content-hamster-reporting` |

### 寫作方法論依賴
Step 07 子代理會自動載入 `hamster-writing-craft` skill 的方法論來優化文章敘事結構。
主 Agent 不需要手動載入該 skill。

---

## 觸發條件

| 關鍵詞 | 動作 |
|--------|------|
| 「影片轉文章」「整理成文章」「寫成解讀文」 | 執行完整流程（Step 01–08，含 06/07 子代理寫作審校 + 07.5 完整性檢查） |
| 「分析這支影片」「擷取簡報截圖」 | 僅執行視覺分析（Step 01–02） |
| 「只要短摘要 / TL;DR」「只要逐字稿」 | **拒絕** — 非本 skill 核心價值 |
| 「先寫初稿與配圖方案」「繁中深度解讀初稿 + figure brief」「不用發佈」且已有 transcript | 可走 transcript-led 輕量模式，讀 `references/transcript-led-draft-plus-figure-brief.md`，產出 article / figure brief / fidelity 三個 artifacts；不得假裝已跑視覺分析或已插入真實截圖 |
| 「找出某大會 / 系列演講，逐篇深度解讀，派 sub agent，主 agent QC，配圖」 | 走 conference / event series batch mode，讀 `references/conference-series-batch-deep-reading.md`；建立系列 manifest，批次派子代理寫 article / figure brief / fidelity，主 agent 統一做文字 QC 與圖片 QA，兩個 gate 都過才發布 |

---

## 執行模式

| 選項 | 說明 |
|------|------|
| ✅ 自動執行 | 觸發後按步驟順序執行，Step 08 強制停等使用者回覆 |
| 🧪 複用性驗證 / Dry-run | 當使用者要求「驗證 skill 複用性」「再派 agent 跑一次看看可不可以」時，先讀 `references/skill-reuse-validation.md`；只能產出文章路徑、contact sheet、Final Gate 結果；**禁止 Notion 上傳、Discord 發布正式稿、Obsidian 同步**，除非使用者在驗證後明確批准發布 |

---

## 執行規範（必須遵守）

> ⚠️ **嚴禁自行發揮替代流程**。每一步的腳本和工具都經過驗證，自行替代會導致路徑錯誤和產出品質問題。

1. **先讀後做**：執行 Step N 前，先讀對應的 reference 文件
2. **逐步驗證**：每步完成後檢查輸出是否符合預期
3. **不跳步驟**：必須按 01→02→...→07 順序執行，禁止跳步
4. **路徑規則**：`${HERMES_SKILL_DIR}` 已由 Hermes 自動展開為本 Skill 的絕對路徑。直接複製貼上指令即可，**絕對不要自行推測或硬編碼路徑**
5. **配圖定位**：本 Skill 的配圖 = **影片原始截圖**（透過 Gemini 分析 + ffmpeg 擷取）。Step 02 和 Step 03 是**預設必做**，不需要使用者明確要求。如果使用者額外需要 AI 生成的插圖，會另外指定使用 `baoyu-article-illustrator` 等生圖 Skill，**v2a 本身不負責 AI 生圖**
6. **Pipeline Checklist**：讀完本 SKILL 後，**第一件事**是呼叫 `todo` 建立 pipeline checklist。每完成一步用 `todo(merge=true)` 更新。Checklist 模板：

```
todo({
  "todos": [
    {"id": "s01", "content": "環境初始化", "status": "pending"},
    {"id": "s02", "content": "Gemini 視覺分析 → analysis.json", "status": "pending"},
    {"id": "s03", "content": "素材擷取 + 品質檢查(delegate) → images/ + manifest.json", "status": "pending"},
    {"id": "s04", "content": "字幕獲取清理 → transcript_clean.txt", "status": "pending"},
    {"id": "s05", "content": "主題地圖萃取 → notes_theme-map.md", "status": "pending"},
    {"id": "s06", "content": "草稿撰寫（純文字）→ article_draft.md", "status": "pending"},
    {"id": "s07", "content": "審校配圖(delegate) → article_draft.md（含圖）", "status": "pending"},
    {"id": "s08", "content": "Final Gate + 預覽 + 交付", "status": "pending"}
  ]
})
```

7. **禁止輪詢腳本狀態**：`video_analyzer.py` 和 `extract_assets.sh` 跑的時候，**不要**用 `ps aux`、`top`、`ls -la` 反覆查看狀態。這些指令的輸出會灌進 context（上次 `ps aux | grep gemini` 一個指令就吃掉 12,000 tokens）。腳本有 timeout 參數，耐心等它結束即可
8. **分析結果讀回門檻**：`video_analyzer.py` 完成後，必須讀回 `analysis.json` 的摘要/關鍵幀/metadata 小切片，再進入主題地圖或寫作；不要只依賴 terminal 長 log，因為 upload/polling log 容易被截斷或灌爆 context。詳見 `references/video-analyzer-readback-and-provider-fallback.md`
9. **禁止手動 Cloudinary 上傳**：Discord 預覽只需發 contact sheet 的路徑或描述。圖片 CDN 上傳由 `notion_hamster_push.py --file` 統一處理，不要在 Step 08 之前手動呼叫 Cloudinary API

### ⚠️ Context Compaction 恢復規則

如果你看到 `[CONTEXT COMPACTION]` 訊息，代表之前的對話被壓縮了。**必須立即執行以下恢復動作**：

1. **重讀本 Skill**：`skill_view(name='video-to-article')` — 重新載入完整規則
2. **讀取 todo list**：`todo()` — 查看 pipeline 進度（compaction 後已自動保留）
3. **確認工作目錄**：`ls {temp_dir}/` 確認已有的產出物
4. **從斷點繼續**：按 todo list 中第一個 `pending` 的步驟繼續，不要重做已完成的步驟

---

## 工作流（9 步）

| Step | 職責 | 執行者 | 參考文件 | 輸入 | 輸出 |
|------|------|--------|---------|------|------|
| 01 | 環境初始化 | 腳本 | — | 使用者觸發 | `{temp_dir}/` |
| 02 | Gemini 視覺分析 | 腳本 | — | 影片來源 | `analysis.json` |
| 03 | 素材擷取 | 腳本 | — | analysis.json + 影片 | `images/` + `manifest.json` |
| 04 | 字幕獲取清理 | 主Agent | `references/workflow-technical.md`, `references/fallbacks.md` | 影片 URL | `transcript_clean.txt` |
| 05 | 主題地圖萃取 | 主Agent | — | 字幕 + analysis.json | `notes_theme-map.md` |
| 06 | 草稿撰寫 | **子代理** | `references/output-format.md` | 主題地圖 + 字幕 | `article_draft.md`（純文字） |
| 07 | 審校配圖 | **子代理** | `references/output-format.md` | 草稿 + 字幕 + manifest | `article_draft.md`（含圖） |
| 07.5 | 完整性檢查（3-stage hybrid） | **子代理** | `hamster-writing-craft` Step 08 | 草稿 + 字幕 | `fidelity_check.md` + 補後 draft |
| 08 | 預覽 + Final Gate + 交付 | 主Agent | `references/deployment-cleanup.md`, dry-run 時加讀 `references/skill-reuse-validation.md` | 完成的文章 + fidelity_check | 預覽 / Gate output / Notion 頁面（需使用者確認後） |

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

**⚠️ 429 / 額度超標時：** 影片已下載至 `metadata.local_video_path`，Gemini 檔案 URI 仍有效。等 30-60 秒後用 `--keep-file --model gemini-2.0-flash` 重試（見 `references/fallbacks.md` §7）。

**⚠️ provider/model 404 時：** 若輔助 vision tool 回傳 `model ... is no longer available` / Gemini 404，這不是可 sleep 重試的暫時錯誤。不要反覆呼叫同一 vision tool；改用本步驟的 `video_analyzer.py --model gemini-2.5-flash`、本地 OCR/PIL，或先修 provider 設定。見 `references/video-analyzer-readback-and-provider-fallback.md`。

**分析結果 readback（必做）：** `video_analyzer.py` 成功後，用小型 parser/讀檔抽出 `content_summary`、`video_info`、高/中重要度 `key_frames`、`gif_segments`、`metadata.local_video_path`/thumbnail/tokens。後續 Step 03–05 以這份 readback 摘要為依據，不要只靠 terminal log。

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
    "tokens": { "input_tokens": 124740, "estimated_cost_usd": 0.019 },
    "youtube_thumbnail_url": "https://img.youtube.com/vi/VIDEO_ID/maxresdefault.jpg",
    "youtube_video_id": "VIDEO_ID"
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

**封面圖：** YouTube 影片的封面圖已自動寫入 `analysis.json` 的 `metadata.youtube_thumbnail_url`。
❌ **不要用 nano-banana-pro 或其他 AI 工具另外生成封面**，直接用 YouTube 縮圖。
在 frontmatter 的 `cover_image` 填入這個 URL 即可。
⚠️ **Step 07/子代理常見漂移：** 審校配圖子代理可能會把 `cover_image` 改成文章內某張本地截圖。主 Agent 在 Step 08 穩定化預覽或發布前必須檢查 frontmatter：若來源是 YouTube，`cover_image` 應恢復為 `analysis.json.metadata.youtube_thumbnail_url`，不要讓代表性截圖覆蓋封面縮圖。

**影片路徑：** `analysis.json` 的 `metadata.local_video_path` 包含已下載影片的本地路徑。`extract_assets.sh` 應使用此路徑，**不要重新下載影片**。

**品質檢查（必做，不可跳過）— 使用 `delegate_task` 執行：**

⚠️ **品質檢查必須用 `delegate_task` 執行**。Vision 回傳會佔大量 context，用子代理做完即丟。

```
delegate_task({
  goal: "品質檢查所有擷取的截圖 and GIF — 含人物幀聯絡單修正",
  context: "工作目錄: {temp_dir}\n影片路徑: 從 {temp_dir}/analysis.json 的 metadata.local_video_path 取得\n\n檢查 {temp_dir}/images/images/ 裡所有截圖和 GIF 的品質。\n\n【第 0 步：讀取 Gemini 描述】\n先用 terminal 讀取 analysis.json 的 key_frames 列表（jq '.analysis.key_frames[] | {timestamp, description}' {temp_dir}/analysis.json），取得每幀的預期內容描述。後續檢查時對照使用。\n\n【最高優先：人物幀偵測與修正】\nGemini 分析的時間戳常有 ±1-2 秒誤差，導致截到講者 talking head 而非投影片。\n處理流程：\n1. 逐張 vision_analyze 每個 frame_*.jpg，question 寫：\n   『Gemini 預期此幀內容為「{對應描述}」。實際圖片主體是：(a) 投影片/圖表/文字內容 (b) 純人物（講者說話、無投影片）。回答 a 或 b，並說明是否與預期描述吻合。』\n2. 對所有判定為 (b) 或「與預期不符」的幀，讀取 analysis.json 取得原始時間戳，用 ffmpeg 在 -2s、-1s、+1s、+2s 共 4 個偏移點重新擷取候選幀：\n   ffmpeg -ss {秒數±偏移} -i {影片路徑} -vframes 1 -q:v 2 -update 1 /tmp/c_{offset}.jpg -y -loglevel error\n3. 執行聯絡單拼圖腳本將這 4 張候選幀合併：\n   python3 {HERMES_SKILL_DIR}/scripts/create_contact_sheet.py /tmp/c_-2.jpg /tmp/c_-1.jpg /tmp/c_+1.jpg /tmp/c_+2.jpg -o /tmp/contact_sheet.jpg\n4. 對聯絡單 /tmp/contact_sheet.jpg 進行一次 vision_analyze，question 寫：\n   『這張聯絡單包含 A, B, C, D 四張備選圖（分別對應 -2s, -1s, +1s, +2s 偏移點），目標是要呈現「{對應描述}」。哪一張圖最符合該描述且是文字清晰定格的簡報？請僅回答單一字母 A, B, C 或 D。如果都包含純人像或不符合，回覆 NONE。』\n5. 根據視覺回覆的代號（例如 A），將最佳候選圖覆蓋原始圖：cp /tmp/c_-2.jpg {原始幀路徑}。若回覆為 NONE，則將該幀從 manifest.json 中刪除。\n\n【其他檢查項目】\n1. 模糊檢查：逐張確認文字清晰可讀、無動態模糊殘影。question 寫：『文字是否清晰可讀、無模糊？回答限 1 句：OK 或描述問題。』\n2. GIF 首尾幀：每個 GIF 用 ffmpeg 擷取首幀 and 尾幀，確認有實質內容不是黑屏。\n   擷取指令：ffmpeg -y -i GIF路徑 -vf \"select='eq(n,0)'\" -frames:v 1 /tmp/gif_first.jpg\n3. 修復模糊幀：用 ffmpeg 在 ±1~2 秒範圍嘗試替換（同樣可優先使用聯絡單一輪判定進行修復）。\n\n【回傳格式】\n只回傳簡短摘要：
- 人物幀：偵測到 N 張 → 修正 M 張 / 刪除 K 張
- 模糊幀：偵測到 N 張 → 修正結果
- GIF 品質：通過/問題
- 最終確認：全部 OK 或仍有問題",
  toolsets: ["vision", "terminal"]
})
```

子代理完成後，主 Agent 只會收到一段簡短的摘要結果（~200 字），不會佔用主 context。

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

### Step 06: 草稿撰寫（delegate_task 子代理）

> ⚠️ **本步驟使用 `delegate_task` 派子代理執行**，不要主 Agent 自己寫。
> 原因：transcript_clean.txt 通常 30k+ tokens，主 Agent 自己讀寫會把 transcript 永久卡在主 context 裡，後續每次 compaction 都重複代價。子代理跑完即丟。

用以下模板呼叫 `delegate_task`（將 `{temp_dir}` 替換為實際工作目錄）：

```
delegate_task(
  goal="撰寫 video-to-article 文章草稿（純文字、不嵌圖）",
  context="工作目錄: {temp_dir}\n\n要讀取的檔案:\n- {temp_dir}/notes_theme-map.md（主題地圖，主結構依據）\n- {temp_dir}/transcript_clean.txt（原始字幕，補細節用）\n- {temp_dir}/analysis.json 的 metadata（影片標題、講者、長度）\n\n寫作規範（先載入再開始工作）:\n1. skill_view(name='video-to-article', file_path='references/output-format.md') — 格式規範與 frontmatter §8\n2. skill_view(name='hamster-writing-craft') — 倉鼠寫作方法論（Opening Hook、認知階梯、數字承載代價、結尾框架、碎碎念默認格式）\n\n任務:\n1. 文章開頭**必須包含 YAML frontmatter**（output-format.md §8 定義的所有必填欄位）\n2. 文章本文從 H2 開始，**不要寫 H1 標題**（Notion Name 屬性已是標題）\n3. 以 notes_theme-map.md 為骨架，按倉鼠寫作方法論擴寫成 Markdown 解讀文\n4. 細節需要回查時，讀 transcript_clean.txt 對應段落（不要把整份 transcript 帶進每個 prompt）\n5. ⚠️ **此步驟先不嵌入圖片**，專注在文字內容的品質和完整度\n6. 遵循 Article-Grade 要求：拒絕過度壓縮，保留 transcript 中的具體數字、原話、人名\n7. 倉鼠碎碎念默認格式：一段 200–300 字口語心得（除非 user 另有要求）\n\n產出:\n- 寫入 {temp_dir}/article_draft.md（純文字版，無圖）\n- 回傳簡短摘要：字數、章節數、frontmatter 欄位列表",
  toolsets=["terminal", "file", "skills"]
)
```

**子代理完成後**，主 Agent **不需要讀 article_draft.md 全文**，只接收摘要即可。後續 Step 07 子代理會自己讀檔。

### Step 07: 審校配圖（delegate_task 子代理）

> ⚠️ **本步驟使用 `delegate_task` 派子代理執行**，不要自己做。
> 子代理有乾淨的 context，不會受到前面步驟的資訊干擾。

用以下模板呼叫 `delegate_task`（將 `{temp_dir}` 替換為實際工作目錄）：

```
delegate_task(
  goal="審校並配圖 video-to-article 文章草稿",
  context="工作目錄: {temp_dir}\n\n要讀取的檔案:\n- {temp_dir}/article_draft.md（純文字草稿）\n- {temp_dir}/transcript_clean.txt（原始字幕）\n- {temp_dir}/manifest.json（圖片索引，每張圖有 article_context 描述對應段落）\n\n寫作規範（先載入再開始工作）:\n1. skill_view(name='video-to-article', file_path='references/output-format.md') — 格式規範\n2. skill_view(name='hamster-writing-craft') — 倉鼠寫作方法論（Opening Hook、論證框架等）\n\n任務（依序執行）:\n\n【Phase 1 - 內容校對 + 寫作優化】\n1. 讀取 transcript_clean.txt，逐段比對 article_draft.md\n2. 補漏遺漏的：重要論點、數據、具體案例、轉化邏輯\n3. 將遺漏內容融入文章對應段落（不是列清單）\n4. 按 hamster-writing-craft 的寫作方法論優化文章結構和表達\n5. 確認術語翻譯一致性\n\n【Phase 2 - 配圖】\n1. 讀取 manifest.json，根據每張圖的 article_context 插入到文章中對應段落之後\n2. Markdown 圖片格式必須是 ![描述文字](圖片路徑)\n   ✅ 正確：![封閉迴路系統架構圖]({temp_dir}/images/frame_03.jpg)\n   ❌ 錯誤：![{temp_dir}/images/frame_03.jpg]()（路徑放在 alt text 裡是錯的！）\n3. 圖片用本地絕對路徑（如 {temp_dir}/images/frame_01.jpg）\n4. ❌ 禁止把圖片堆在文章最後面（append）——每張圖必須出現在它描述的內容附近\n5. ❌ 禁止連續兩張圖——「連續」的定義是兩張圖之間只有空白行，沒有實質文字。如果兩張圖之間沒有至少一段有意義的中文文字（不算空行），必須合併成一張或在中間加轉場說明\n6. 每篇文章至少 3 張配圖\n7. 每張圖的 alt text 要有描述性（不要寫「圖片」）\n8. ❌ 講者影像數量限制（最重要！）：\\n   - 「講者影像」= 畫面主體是講者本人、沒有投影片/圖表/文字內容的截圖（包括：純臉部特寫、講者坐在桌前說話、講者站在舞台上沒有投影片背景）\\n   - 整篇文章最多只能有 **1 張**講者影像（用於介紹講者段落）\\n   - 如果 manifest 裡有多張講者影像，只選最清晰的 1 張，其餘全部跳過\\n   - 投影片截圖背景裡有講者小窗（picture-in-picture）不算講者影像，可以正常插入\n\n【Phase 3 - 格式檢查 + 自我驗證】\n1. 用 terminal 執行 grep -o '<[^>]*>' article_draft.md 確認無 HTML tag\n2. em dash、U+2015、雙逗號與簡轉繁由 Step 08 主 Agent Final Gate 統一處理；子代理不要自行用 sed/awk 亂改，但若有改文或補圖，仍必須重新跑連續圖片檢查\n3. ⚠️ 必須執行以下自我驗證指令確認沒有連續圖片：\n   python3 -c \"\nwith open('{temp_dir}/article_draft.md') as f:\n    lines = f.readlines()\nimgs = [i for i,l in enumerate(lines) if l.strip().startswith('![')]\nfor j in range(len(imgs)-1):\n    between = lines[imgs[j]+1:imgs[j+1]]\n    if not any(l.strip() and not l.strip().startswith('![') for l in between):\n        print(f'ERROR: 連續圖片 L{imgs[j]+1} & L{imgs[j+1]+1}')\nassert all(any(l.strip() and not l.strip().startswith('![') for l in lines[imgs[j]+1:imgs[j+1]]) for j in range(len(imgs)-1)), '有連續圖片！'\nprint('OK: 無連續圖片')\n\"\n   如果驗證失敗，必須修正後重新驗證\n\n完成後用 terminal 工具寫回 {temp_dir}/article_draft.md。⚠️ 若 {temp_dir} 位於 /var/folders/ 等 macOS temp/sensitive path，禁止使用 patch/write_file 工具（會被拒絕或造成 mutation verifier 誤報）；改用 terminal 執行 Python 腳本原地讀寫，完成後用 read_file/terminal 驗證圖片數與關鍵修改確實存在。",
  toolsets=["terminal", "file", "skills", "vision"]
)
```

**子代理完成後**，主 Agent 讀取 `article_draft.md` 確認圖片已正確嵌入，然後進入 Step 07.5。

### Step 07.5: 完整性檢查（delegate_task 子代理，3 階段 hybrid）

> ⚠️ **本步驟使用 `delegate_task` 派子代理執行**。
> ⚠️ **macOS temp path 寫檔坑**：若 `{temp_dir}` 位於 `/var/folders/...` 等 temp/sensitive path，fidelity checker 不得用 `write_file` / `patch` 寫入 `fidelity_check.md`，安全層可能拒絕但摘要仍聲稱成功。必須改用 `terminal` 執行 Python 腳本寫檔，並讀回確認 `fidelity_check.md` 存在、大小合理、schema 完整。
> 為什麼還需要：Step 07 子代理已部分校對，但角色繁重（校對 + 寫作優化 + 配圖 + 格式檢查），fidelity 容易被稀釋。本步驟用乾淨 context 的 fidelity-checker 做最後一次嚴格比對，並輸出**透明 log + 行號 reference**，讓主 Agent 可以隨需 fetch transcript 對應段落判斷 nice_to_have。

用以下模板呼叫 `delegate_task`：

```
delegate_task(
  goal="完整性檢查 video-to-article 文章對 transcript 的忠實度（3-stage hybrid）",
  context="工作目錄: {temp_dir}\n\n要讀取的檔案:\n- {temp_dir}/article_draft.md（已配圖的最終 draft）\n- {temp_dir}/transcript_clean.txt（原始字幕，唯一 source of truth）\n\n方法論依據（先載入）:\nskill_view(name='hamster-writing-craft', file_path='SKILL.md') — 看『寫作後完整性檢查（Step 08）』章節，照三類元素（數字/反直覺金句/具名故事）+ 三選一判斷（critical/nice_to_have/out_of_scope）\n\n任務（嚴格依序執行）:\n\n【Stage 1: 找 missing items + 三級分類】\n1. 讀 transcript_clean.txt，標記每行的 1-based 行號（用 grep -n 或 awk '{printf \"L%d: %s\\\\n\", NR, $0}'）\n2. 抽出三類高價值元素：\n   - 數字（金額、時間、百分比、版本號、量級對比）\n   - 反直覺金句（「不是 X 而是 Y」「居然」「反而」）\n   - 具名故事（人名 + 動詞 + 結果）\n3. 對每個元素，反向 grep article_draft.md 看有沒有引用（注意：圖片 ![...]() 行不算內文，跳過）\n4. 對 missing items 分三級（依倉鼠寫作方法論的判斷）：\n   - **critical**: 訪談主論點被漏（會讓文章誤導讀者，必須補）\n   - **nice_to_have**: 強化型細節（補了更好，不補也成立 — 留給主 Agent 判斷）\n   - **out_of_scope**: 離題、重複、純客套（ignore）\n\n【Stage 2: 條件式自動補（critical 與 nice_to_have 均主動融入）】\n- 對每個 critical item，找到 article 中最適合插入的位置（通常是同主題段落）\n- 改寫 article_draft.md 把 critical 內容融入該段（不是另開新段、不是列清單）\n- nice_to_have 項目補入時，可做適度段落擴寫或新增子段落以確保最完整的技術覆蓋度，僅 out_of_scope 的客套或離題內容可以直接忽略。\n- 補完後重跑「無連續圖片」自我驗證指令（從 Step 07 borrow，避免破壞圖片佈局）\n\n【Stage 3: 輸出透明 log】\n寫入 {temp_dir}/fidelity_check.md，格式（嚴格依此 schema，後續主 Agent 會 parse）：\n\n```markdown\n## 完整性檢查 — <article_title>\n\n生成時間: <ISO timestamp>\nTranscript: {temp_dir}/transcript_clean.txt\nDraft: {temp_dir}/article_draft.md\n\n### 已自動補入 draft (critical)\n- ✅ <一句話描述>  (transcript:L142-L168)\n  插入位置: H2「<段落標題>」之後\n\n### 待主 Agent / user 判斷 (nice_to_have)\n- ⚠️ <一句話描述>  (transcript:L210-L215)\n  建議: 強化「<某段>」的論點\n- ⚠️ <一句話描述>  (transcript:L380-L385)\n  建議: 開新支線『<暫擬標題>』，需評估是否值得加段落\n\n### 已忽略 (out_of_scope)\n- ❌ <一句話描述>  (transcript:L5-L12)\n  理由: 純客套 / 重複 / 離題\n\n### 摘要\n- transcript 抽出元素: <N> 個\n- 文章已引用: <X> 個\n- 已自動補入: <Y> 個 (critical)\n- 待判斷: <Z> 個 (nice_to_have)\n- 已忽略: <W> 個 (out_of_scope)\n```\n\n回傳格式（給主 Agent 看的摘要，~200 字以內）:\n- critical 補入: <Y> 個 — 列前 3 個 + 行號\n- nice_to_have 待判斷: <Z> 個 — 列前 3 個 + 行號\n- 自動補入後 draft 有無破圖: 通過/失敗",
  toolsets=["terminal", "file", "skills"]
)
```

**子代理完成後**，主 Agent：
1. 讀取 `fidelity_check.md`（小檔，僅~500–1000 字）
2. 對 nice_to_have 列表逐一判斷：
   - 不確定要不要加 → `Read({temp_dir}/transcript_clean.txt, offset=<起始行>, limit=<行數>)` 抓對應段落看清楚再決定
   - 決定加 → 直接編輯 article_draft.md（小幅修改，主 Agent 自己做即可）
   - 決定不加 → 跳過
3. 檢查 fidelity checker 額外註記的「未在 transcript 找到依據」或「僅 analysis/source claim 支撐」的說法。若該 claim 不是影片逐字稿可驗證事實，發布前要改成較保守表述（例如「影片把這件事放在源碼級上下文管理裡拆解」），或明確標成「影片主張」，不要讓未驗證數字變成文章肯定句。
4. **不需要載入整份 transcript**，所有 fetch 都按行號 on-demand
5. 進入 Step 08 publish

### Step 08: 預覽 + 交付（🛑 強制中斷點）

> **執行前必讀**：`references/deployment-cleanup.md`
> 若本次是複用性驗證 / Dry-run，還必須先讀 `references/skill-reuse-validation.md`，並以該文件的 Final response contract 回報。

**模式分流：**
- 正式交付：先預覽 → 等待使用者確認 → 根據反饋修正 → 最後一次修改後跑 Final Gate → 使用者明確批准後才發布。
- Dry-run / 複用性驗證：不發布、不等發布批准；可以產出 contact sheet 與本地文章路徑，但必須在 final response 前跑 Final Gate，並附完整 Gate output。

**預覽：**
1. 讀取 `fidelity_check.md`（Step 07.5 子代理輸出）
2. 對 nice_to_have 列表逐一判斷：必要時 `Read(transcript_clean.txt, offset=<行>, limit=<N>)` 抓對應段落，決定是否補入 article_draft.md
3. 讀取最終 `article_draft.md`
4. **穩定化預覽產物（必做）**：若工作目錄在 `/var/folders/...` 或其他 temp 路徑，先依 `references/stable-preview-artifacts.md` 將 `article_draft.md`、`contact_sheet.jpg`、`fidelity_check.md`、`notes_theme-map.md` 與 `outputs/images/` 複製到 `/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/<VIDEO_ID>/`，並把文章內圖片路徑替換成穩定目錄後，對穩定稿重跑 `final_gate.py --check-only`。Discord 預覽與後續 Notion 上傳都優先使用穩定稿，避免 temp 清理或 compaction 後圖片失效。
5. 用 Discord embed 分段預覽文章內容（每段一張卡片）
6. 用 Discord embed 預覽每張配圖（含 alt text）

**交付：**
1. 將校對後的 `article_draft.md` 與素材清單提交給使用者
2. **在此停下，等待使用者回覆**（同時可附 `fidelity_check.md` 摘要讓 user 知道哪些 nice_to_have 沒採用）
3. 根據反饋修正
4. **發布前 Final Gate（主 Agent 必跑，即使 Step 07 子代理已跑過）**：
   - 若主 Agent 在 Step 07 之後有任何手動插圖、替換圖片 URL、增刪段落，必須在最後一次修改後重新執行 Final Gate。
   - Final Gate 會先做 deterministic normalization：`zhtw` 台灣用語轉換 → OpenCC `s2tw` 補漏字 → U+2014/U+2015 轉全形逗號 → 壓掉 `，，`。
   - Final Gate 會阻擋：本文 `---` divider、連續圖片、HTML tag、dash residue、中英黏連。完整英文句可能是引用或專有語句，不作為阻擋項；由人工審稿判斷是否需要翻譯。
   - 必跑以下指令；如果輸出不是 `OK: final article gate passed`，禁止發布：
     ```bash
     python3 ${HERMES_SKILL_DIR}/scripts/final_gate.py /absolute/path/to/article_draft.md
     ```
   - 只想檢查、不想寫回 normalization 時可加 `--check-only`，但正式發布前必須跑不帶 `--check-only` 的版本。
5. 依使用者指示發布：
   ```bash
   # ✅ Agent-friendly CLI：frontmatter 中的 tags/url/note/cover 會自動讀取
   # ❌ 不要再手動傳 --tags --url --note --image，那些已在 frontmatter 裡
   # ⭐ cover_image：YouTube 影片直接用 analysis.json 裡的 youtube_thumbnail_url
   # ⚠️ 圖片路徑可保持本地路徑；腳本自動上傳 Cloudinary、替換 Notion 內容，並預設寫回 source
   python3 ~/.hermes/skills/openclaw-imports/circleghost-content-hamster-reporting/scripts/python/notion_hamster_push.py \
     publish --file article_draft.md --json
   ```
   推送成功後會自動生成 `notion_manifest.json`（image→block_id 映射）。

   **修復圖片/更新文章**：用 `--update` 模式重新推送整篇文章：
   ```bash
   python3 ~/.hermes/skills/openclaw-imports/circleghost-content-hamster-reporting/scripts/python/notion_hamster_push.py \
     update --page-id <PAGE_ID> --file article_draft.md --json
   ```

6. 複製到 Obsidian：`cp article_draft.md ~/Desktop/同步知識庫/30_Projects/倉鼠特報/發佈區/`
7. 完成後執行 `bash ${HERMES_SKILL_DIR}/scripts/cleanup_temp_dirs.sh`

> ⚠️ **注意**：`/var/folders/` 等 temp 路徑會被 `write_file` 工具拒絕。
> 寫入文章時請用 `terminal` 工具（如 `cat > article_draft.md << 'EOF'`）。

---

## 環境需求

## References / support files

- `references/video-analyzer-readback-and-provider-fallback.md` — provider/model 404 handling, mandatory `analysis.json` readback, and embedded-X-video writing handoff split.
- `references/gemini-cap-text-only-fallback.md` — Gemini monthly spending-cap fallback: continue as a transparent transcript-led deep reading when captions are usable, with no images or unverified visual claims.
- `references/transcript-led-code-with-claude-series-example.md` — Concrete session note for a long podcast run: how to mark visual steps blocked, convert Step 07 into editorial review, preserve transparency, and handle Final Gate after normalization fails on zh-en spacing.
- `references/transcript-led-invalid-visual-qc.md` — Visual extraction/QC fallback when Gemini/extractor produces zero usable assets or mismatched frames: cancel Step 03, continue transcript-led, prohibit visual claims/placeholders, and avoid inventing key frames to satisfy extractor scripts.
- `references/transcript-led-draft-plus-figure-brief.md` — 輕量模式：已有 transcript、使用者只要繁中深度解讀初稿與配圖方案時，產出 article / figure brief / fidelity 三檔，並明確標示未跑視覺分析與未插入真實截圖。
- `references/conference-series-batch-deep-reading.md` — 大會 / 活動系列影片批次深度解讀：manifest-first、sub-agent 分批寫作、主 agent text QC + image QA 雙 gate、未通過圖片 QA 時禁止發布。
- `references/conference-batch-text-artifact-gates.md` — 大會批次的 transcript-led 文字包檢查：article / figure brief / fidelity 三件套、概念圖 brief 規格、證據表與 batch validator gates。
- `references/code-with-claude-transcript-led-batch-notes.md` — Code with Claude 系列 transcript-led 批次補充：ASR 將 Claude 誤轉 Cloud 的透明處理、三件套 gate、frontmatter divider validator 坑與最小 patch loop。
- `references/code-with-claude-series-24-artifact-validation.md` — Code with Claude #24 三件套實例補充：manifest path resolution、strict validator 下 support artifacts 避免 H1、hamster_note 單獨補長、fidelity disclosure。

## 環境需求
## 環境需求

| 類型 | 需求 |
|------|------|
| 系統工具 | `yt-dlp`, `ffmpeg`, `ffprobe` |
| Python | `python3` + `google-genai` |
| 環境變數 | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` |
