---
name: video-to-article
description: |
  倉鼠影片深度解讀 pipeline。當使用者說「解讀這個影片」「把這影片整理成文章」「用倉鼠寫文 skill」「分析這支影片」「擷取簡報截圖」「影片轉文章」「v2a」時觸發。
  從 YouTube 或本地影片做 Gemini 視覺分析、字幕萃取、證據截圖 / GIF、主題地圖、深度解讀草稿與 Final Gate，最後停在預覽確認並 handoff 給 notion-upload-workflow。
  不適用於：短摘要、逐字稿、純翻譯、多影片整合；AI 概念配圖另交給 baoyu-article-illustrator + hamster-image-generation。
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

### Cross-skill contract

- **寫作方法論**：Step 06 初稿與 Step 07 主編審校都載入 `hamster-writing-craft`。Step 06 就要寫出有讀者入口的深度解讀，不可先交摘要味草稿再補救。
- **影片證據圖**：本 skill 只負責影片 evidence frames / GIF，並用視覺驗證確認截圖不是空框、模糊投影片或無資訊過渡幀。
- **AI 概念配圖**：若需要每個 H2 的 baoyu 概念資訊圖，handoff 給 `creative/baoyu-article-illustrator` 規劃，再交 `hamster-image-generation` 生圖與 QA。
- **發布上傳**：Notion / Cloudinary / 遠端圖片驗證交給 `notion-upload-workflow`；本 skill 在 Step 08 預覽確認點停止，不自行重複上傳流程。

### Skill eval seed set

後續要檢查本 pipeline 的觸發準確率與流程遵循率時，使用 `references/eval-prompts.md`。評估時看 transcript，不只看最後文章：todo 是否建立、Step 06/07 是否載入 writing craft、截圖是否視覺驗證、Step 08 是否停在預覽確認。

---

## 觸發條件

| 關鍵詞 | 動作 |
|--------|------|
| 「影片轉文章」「整理成文章」「寫成解讀文」 | 執行完整流程（Step 01–08，含 06/07 子代理寫作審校 + 07.5 完整性檢查） |
| 「分析這支影片」「擷取簡報截圖」 | 僅執行視覺分析（Step 01–02） |
| 「只要短摘要 / TL;DR」「只要逐字稿」 | **拒絕** — 非本 skill 核心價值 |
| 「先寫初稿與配圖方案」「繁中深度解讀初稿 + figure brief」「不用發佈」且已有 transcript | 可走 transcript-led 輕量模式，讀 `references/transcript-led-draft-plus-figure-brief.md`，產出 article / figure brief / fidelity 三個 artifacts；不得假裝已跑視覺分析或已插入真實截圖 |
| 使用者明確說「這是 podcast／演講／keynote」「不用 v2a 送 Gemini 分析」「不要跑影片視覺分析」，但仍要深度解讀或上傳 Notion | 立刻切換 transcript-led 模式：取消 Step 02–03 的 Gemini 視覺分析、影片截圖與視覺 QA，先抓字幕 / ASR → 主題地圖 → 深度解讀 → fidelity check；不可寫任何畫面 / 截圖 / 投影片 claim。只有使用者另外要求文章配圖時，才 handoff `creative/baoyu-article-illustrator` + `hamster-image-generation`；Notion 發布仍 handoff `notion-upload-workflow`。字幕來源與滾動字幕重複檢查見 `references/transcript-led-speech-and-subtitle-validation.md`。 |
| 「找出某大會 / 系列演講，逐篇深度解讀，派 sub agent，主 agent QC，配圖」 | 走 conference / event series batch mode，讀 `references/conference-series-batch-deep-reading.md`；建立系列 manifest，批次派子代理寫 article / figure brief / fidelity，主 agent 統一做文字 QC 與圖片 QA，兩個 gate 都過才發布 |
| 「Review 已完成的大會系列文章 01-08 against transcripts」「produce deep-reading + terminology improvement artifacts」 | 走 existing-article review mode，讀 `references/conference-batch-existing-article-review.md`；不要重寫或發布文章，產出逐篇 review + batch summary，標 P0/P1/P2 與術語白話化建議 |

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
9. **禁止手動 Cloudinary 上傳**：Discord 預覽只需發 contact sheet 的路徑或描述。Notion 發布與圖片 CDN 上傳統一交給 `notion-upload-workflow`，不要在 Step 08 之前手動呼叫 Cloudinary API，也不要在本 Skill 複製 Notion 上傳細節

### ⚠️ Context Compaction 恢復規則

如果你看到 `[CONTEXT COMPACTION]` 訊息，代表之前的對話被壓縮了。**必須立即執行以下恢復動作**：

1. **重讀本 Skill**：`skill_view(name='video-to-article')` — 重新載入完整規則
2. **讀取 todo list**：`todo()` — 查看 pipeline 進度（compaction 後已自動保留）
3. **確認工作目錄**：`ls {temp_dir}/` 確認已有的產出物
4. **從斷點繼續**：按 todo list 中第一個 `pending` 的步驟繼續，不要重做已完成的步驟

---

## 工作流（9 步 + 可選概念配圖）

| Step | 職責 | 執行者 | 參考文件 | 輸入 | 輸出 |
|------|------|--------|---------|------|------|
| 01 | 環境初始化 | 腳本 | — | 使用者觸發 | `{temp_dir}/` |
| 02 | Gemini 視覺分析 | 腳本 | — | 影片來源 | `analysis.json` |
| 03 | 素材擷取 | 腳本 | — | analysis.json + 影片 | `images/` + `manifest.json` |
| 04 | 字幕獲取清理 | 主Agent | `references/workflow-technical.md`, `references/fallbacks.md` | 影片 URL | `transcript_clean.txt` |
| 05 | 主題地圖萃取 | 主Agent | — | 字幕 + analysis.json | `notes_theme-map.md` |
| 06 | 草稿撰寫（Writing Craft 初稿） | **子代理** | `references/output-format.md` + `hamster-writing-craft` | 主題地圖 + 字幕 | `article_draft.md`（純文字，已套前言 Gate / 認知階梯 / 碎碎念） |
| 07 | 審校 + 影片證據圖 placement | **子代理** | `references/output-format.md` + `hamster-writing-craft` | 草稿 + manifest | `article_draft.md`（含 evidence frames / GIF） |
| 07.5 | 完整性檢查（3-stage hybrid） | **子代理** | `hamster-writing-craft` Step 08 | 草稿 + 字幕 | `fidelity_check.md` + 補後 draft |
| 07.6 | 可選：文章概念配圖 handoff | 主Agent / 子代理 | `creative/baoyu-article-illustrator` + `hamster-image-generation` | 已審校文章 + H2 list | `illustrations/` + `qa-contact-sheet` + 含 concept figures 的 draft |
| 08 | 預覽 + Final Gate + 交付 | 主Agent | `references/deployment-cleanup.md`, dry-run 時加讀 `references/skill-reuse-validation.md` | 完成的文章 + fidelity_check | 預覽 / Gate output / 穩定稿路徑；Notion 發布交給 `notion-upload-workflow` |

### Cross-skill handoff：影片證據圖 vs 文章概念圖

`video-to-article` 只負責影片處理與 pipeline orchestration，不把所有配圖責任都攬進本 skill。遇到「深度解讀 + 配圖」任務時，先分清三種資產：

| 資產類型 | 角色 | 負責 skill | 何時使用 |
|---|---|---|---|
| `evidence_frames` / GIF | 影片證據圖：證明影片裡真的有這個畫面 | `video-to-article` Step 02–03、Step 07 | 預設使用，尤其是簡報頁、產品畫面、操作流程、原始圖表 |
| `concept_figures` | 文章概念圖：解釋 H2 論點、框架、對比、流程 | `creative/baoyu-article-illustrator` + `hamster-image-generation` | 使用者要求「幫文章配圖」「每個 H2 配圖」「baoyu 概念資訊圖」或文章需要更豐富圖文節奏 |
| `cover_image` | 入口封面 | YouTube 來源預設 `analysis.json.metadata.youtube_thumbnail_url`；明確要求才走生圖 | 不要為了每篇 v2a 自動生封面 |

**標準策略：** 文章可以同時有影片截圖 / GIF 與概念資訊圖，但兩者要在 Markdown 中清楚分工：證據圖放在引用影片內容附近，概念圖放在 H2 或關鍵框架段落之後。不要把概念圖當成影片證據，也不要為了補圖而把無意義 talking head 塞進文章。

**Notion handoff：** 本 skill 不複製 Notion / Cloudinary 上傳細節。Step 08 只產出通過 Final Gate 的穩定稿路徑與素材清單；使用者確認發布後，必須載入 `notion-upload-workflow`，由該 skill 執行 preflight / publish / inspect / 遠端驗證。

---

## 各步驟詳細說明

### Step 01: 環境初始化

> 直接執行以下指令（`${HERMES_SKILL_DIR}` 已自動展開，不需修改）：

```bash
bash ${HERMES_SKILL_DIR}/scripts/prepare_temp_dir.sh
```

建立本次 session 專屬暫存目錄，後續所有中繼檔案存於此。

#### Gemini 認證 preflight（執行 Step 02 前）

`video_analyzer.py` 需要目前 subprocess 已匯出 `GEMINI_API_KEY` 或 `GOOGLE_API_KEY`。不要因為 canonical `.env` 裡看得到 key 名稱，就假設 Python subprocess 一定拿得到。

1. 先做**只檢查是否存在、不輸出 secret**的 preflight。
2. 若目前環境沒有 key，但 canonical Hermes `.env` 有設定，使用能正確解析 dotenv quoting 的方式載入；**不要直接 `source ~/.hermes/.env`**，因為同檔其他含空白路徑的值若未正確引用，可能讓 shell 在載入途中產生無關錯誤。
3. 認證補齊後，重新執行同一個 analyzer command；成功重試代表 setup 已恢復，不要把第一次缺環境變數記成 provider 故障。
4. 長影片的 Gemini File API processing + analysis 可能接近或超過單次前景工具的 600 秒上限。這類有明確終點的 bounded job 應使用 background + completion notification；不要用 `ps`、`top` 或目錄輪詢灌入大量 log。

可重用做法與安全檢查範例見 `references/gemini-auth-preflight-and-long-run.md`。

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
| `<影片來源>` | 本地路徑或 YouTube URL。若使用者提供 `https://www.youtube.com/live/VIDEO_ID?...`，先正規化成 `https://www.youtube.com/watch?v=VIDEO_ID`，再傳給 `video_analyzer.py` / `get_transcript.py` / `yt-dlp`，避免 `/live/` URL 在部分路徑被誤判成本地檔案路徑。詳見 `references/youtube-live-url-and-final-gate-normalization-pitfalls.md`。 |
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

**⚠️ 429 / 額度超標時：** 影片已下載至 `metadata.local_video_path`，Gemini 檔案 URI 仍有效。先讀實際腳本的 `DEFAULT_MODEL`，不要照舊文件硬指定模型。2026-07-18 的腳本預設為 `gemini-3-flash-preview`；長影片若需重試，優先切成約 60 分鐘段落，分段分析後加回 timestamp offset。完整做法見 `references/gemini3-segmented-visual-retry.md`。

**⚠️ provider/model 404 時：** 若輔助 vision tool 回傳 `model ... is no longer available` / Gemini 404，這不是可 sleep 重試的暫時錯誤。不要反覆呼叫同一 vision tool；改用本步驟的 `video_analyzer.py --model gemini-2.5-flash`、本地 OCR/PIL，或先修 provider 設定。見 `references/video-analyzer-readback-and-provider-fallback.md`。

**⚠️ 整片推理完成但 JSON parse 失敗時：** 若 log 顯示 Gemini `generateContent` 200、tokens/cost 已產生，最後因 `duration_seconds: 104:28` 之類非法 JSON 報 `Expecting ',' delimiter`，不要把它回報成視覺分析不可用，也不要依截斷的 `raw_response_preview` 手補 key frames。對超過約 60 分鐘的影片，直接依 `references/gemini3-segmented-visual-retry.md` 複用本地原片切段重跑；各段 prompt 強制 `video_info.duration_seconds` 使用純整數秒數，只有 `timestamp` 使用 `MM:SS`。成功分段只重跑失敗 part，最後保留 `source_part`、`timestamp_seconds` 與原始高解析影片絕對路徑再合併。

**分析結果 readback（必做）：** `video_analyzer.py` 成功後，用小型 parser/讀檔抽出 `content_summary`、`video_info`、高/中重要度 `key_frames`、`gif_segments`、`metadata.local_video_path`/thumbnail/tokens。後續 Step 03–05 以這份 readback 摘要為依據，不要只靠 terminal log。

**長影片推理成功但 JSON parse 失敗：** 若 Gemini HTTP / token 計費與 analysis 均完成，最後只因 `duration_seconds: 104:28` 這類未加引號時間格式導致 JSON 解析失敗，不要誤判成 provider 故障。保留原始影片，切成約 60 分鐘無音訊段落，prompt 明定 `duration_seconds` 必須是純整數、只有 `timestamp` 可用 `MM:SS`，再分段分析與 offset 合併。完整做法與 accepted-only 二次視覺 QA 見 `references/long-video-json-parse-and-second-pass-visual-qa.md`。

**大影片處理 timeout fallback（可恢復視覺分析）：** 若原始高解析影片上傳成功但 Gemini File API server-side processing 長時間停在 `PROCESSING` 並由腳本 10 分鐘 timeout，不要直接退回純字幕版。先讀 `references/gemini-visual-proxy-analysis.md`，建立 `fps=1,scale=-2:360`、無音訊的 visual proxy 交給 Gemini 分析時間戳，再用原始影片抽取最終高解析截圖。這個 fallback 需要在回報中透明標示「Gemini 看的是降解析 proxy，文章截圖來自原始影片」。

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

**大影片 proxy 注意：** 若 Step 02 使用 `references/gemini-visual-proxy-analysis.md` 的 downsampled visual proxy 完成分析，Step 03 的 `<影片路徑>` 必須改回原始高解析影片，不要用 proxy 抽圖。若 `extract_assets.sh` 因 `frame_aligner.py` 依賴或微對齊失敗而中止，可用 ffmpeg 依 `analysis.json` 的已篩選時間戳直接抽幀，並手寫相容 `manifest.json`，但仍必須做 contact sheet + vision QA。

**輸出：**
- `images/frame_NN_MM_SS.jpg` — 關鍵截圖
- `images/gif_NN_MM_SS-MM_SS.gif` — 動態片段（≤12 秒）
- `manifest.json` — 整合索引

**封面圖：** YouTube 影片的封面圖已自動寫入 `analysis.json` 的 `metadata.youtube_thumbnail_url`。
❌ **不要用 nano-banana-pro 或其他 AI 工具另外生成封面**，直接用 YouTube 縮圖。
在 frontmatter 的 `cover_image` 填入這個 URL 即可。
⚠️ **Step 07/子代理常見漂移：** 審校配圖子代理可能會把 `cover_image` 改成文章內某張本地截圖。這是錯誤行為：Step 07 可以插入 evidence frames / GIF 到正文，但**不得修改 YouTube 來源文章的 `cover_image`**。主 Agent 在 Step 08 穩定化預覽或發布前必須檢查 frontmatter：若來源是 YouTube，`cover_image` 應恢復為 `analysis.json.metadata.youtube_thumbnail_url`（或 `https://img.youtube.com/vi/<VIDEO_ID>/maxresdefault.jpg`），不要讓代表性截圖覆蓋封面縮圖。穩定複製到 profile output 後、Final Gate 前也要再檢查一次，因為子代理改過的 frontmatter 會被一起複製。

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

**主 Agent 最終視覺覆核（不可省略）：** 子代理 QA 通過後，主 Agent仍要親眼檢查最終 contact sheet；對 benchmark、圖表、UI、文字密集投影片，還要逐張開啟完整解析度，確認沒有被 macOS 權限視窗、更新提示、瀏覽器 popover 或游標遮住。Contact sheet 縮圖可能把遮擋藏起來。若需以 ±2 秒候選修復，或文章使用超過四個媒體，依 `references/stable-preview-artifacts.md` 的 dense-slide 與 explicit-xstack 流程重建最終 contact sheet，並確認它精確對應文章實際使用的 frames 與 GIF 首幀。

**Contact sheet 腳本上限：** `scripts/create_contact_sheet.py` 一次最多使用 4 張輸入；超過時雖會輸出成功訊息，實際只取前 4 張並印 warning。大量 evidence frames 不可用 12 張一批後假設全部入圖；應嚴格每批 ≤4 張，或改用 `references/stable-preview-artifacts.md` 的 explicit-xstack 流程，並核對 sheet 數量與 frame 數能完整對應。

### Step 04: 字幕獲取與清理

> **執行前必讀**：`references/workflow-technical.md` + `references/fallbacks.md`

- 優先用 `youtube-transcript-api` 或 `yt-dlp` 下載字幕；所有字幕抓取都必須套 429-safe policy：語言白名單（禁 `all`）、`--sleep-subtitles 60` / 請求前 sleep、批次切分與快取
- 去除時間碼，合併破碎短句 → `transcript_clean.txt`
- 若字幕品質檢查後更換了 source（例如自動字幕有 rolling-caption 三重複句，後來取得人工字幕），不得讓舊、新子代理並行寫同一個 `notes_theme-map.md`。依 `references/transcript-source-swap-and-stale-subagent-writes.md` 使用 versioned canonical transcript、分離輸出路徑、provenance/hash 驗身分，再 promotion；既有草稿必須對 canonical transcript 重跑 fidelity。
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
  context="工作目錄: {temp_dir}\n\n要讀取的檔案:\n- {temp_dir}/notes_theme-map.md（主題地圖，主結構依據）\n- {temp_dir}/transcript_clean.txt（原始字幕，補細節用）\n- {temp_dir}/analysis.json 的 metadata（影片標題、講者、長度）\n\n寫作規範（先載入再開始工作）:\n1. skill_view(name='video-to-article', file_path='references/output-format.md') — 格式規範與 frontmatter §8\n2. skill_view(name='hamster-writing-craft') — 倉鼠寫作方法論。Step 06 的初稿就要完整套用 writing craft，不是先寫普通摘要再晚點修；必須依序通過「讀者進場前言 Gate」、Opening Hook、認知階梯、數字承載代價、結尾框架、碎碎念默認格式\n\n任務:\n1. 文章開頭**必須包含 YAML frontmatter**（output-format.md §8 定義的所有必填欄位）\n2. 文章本文從 H2 開始，**不要寫 H1 標題**（Notion Name 屬性已是標題）\n3. 以 notes_theme-map.md 為骨架，按倉鼠寫作方法論擴寫成 Markdown 解讀文\n4. 細節需要回查時，讀 transcript_clean.txt 對應段落（不要把整份 transcript 帶進每個 prompt）\n5. ⚠️ **此步驟先不嵌入圖片**，專注在文字內容的品質和完整度\n6. 遵循 Article-Grade 要求：拒絕過度壓縮，保留 transcript 中的具體數字、原話、人名\n7. 倉鼠碎碎念默認格式：一段 200–300 字口語心得（除非 user 另有要求）\n\n產出:\n- 寫入 {temp_dir}/article_draft.md（純文字版，無圖）\n- 回傳簡短摘要：字數、章節數、frontmatter 欄位列表",
  toolsets=["terminal", "file", "skills"]
)
```

**子代理完成後**，先驗證目標 artifact 是否已落地，再判斷是否需要重派：

- `delegate_task` 回傳 `timeout` 不等於工作失敗。先用絕對路徑檢查 `article_draft.md`、`fidelity_check.md` 等預期產物是否存在、非空，並讀取檔案頭部與尾部確認內容完整。
- 若 artifact 已存在，接管下游流程，不要因 timeout 重做整個步驟；回報時透明標示「子代理逾時，但產物已驗證落地」。
- 若 artifact 不存在或內容不完整，才重派子代理，並縮小任務範圍。
- 穩定化複製後，Final Gate 必須使用實際建立的絕對路徑重新執行；影片 ID 或目錄名稱容易有字元誤抄，`file not found` 要先核對路徑，不要把它判成產物遺失。

**子代理完成後**，主 Agent 不需要讀 article_draft.md 全文，直接進入 Step 07 子代理。

### Step 07: 審校配圖（delegate_task 子代理）

> ⚠️ **本步驟使用 `delegate_task` 派子代理執行**，不要自己做。
> 子代理有乾淨的 context，不會受到前面步驟的資訊干擾。

用以下模板呼叫 `delegate_task`（將 `{temp_dir}` 替換為實際工作目錄）：

```
delegate_task(
  goal="審校並配圖 video-to-article 文章草稿",
  context="工作目錄: {temp_dir}\n\n要讀取的檔案:\n- {temp_dir}/article_draft.md（純文字草稿）\n- {temp_dir}/transcript_clean.txt（原始字幕）\n- {temp_dir}/manifest.json（圖片索引，每張圖有 article_context 描述對應段落）\n\n寫作規範（先載入再開始工作）:\n1. skill_view(name='video-to-article', file_path='references/output-format.md') — 格式規範\n2. skill_view(name='hamster-writing-craft') — 倉鼠寫作方法論（Opening Hook、論證框架等）\n\n任務（依序執行）:\n\n【Phase 1 - 主編審校 + 前言 Gate】\n1. 重新載入 hamster-writing-craft，先檢查前言是否通過「讀者進場前言 Gate」；若只是摘要、空泛稱讚或元敘述開場，必須重寫前言\n2. 檢查文章結構是否符合 Opening Hook、認知階梯、數字承載代價、結尾框架與碎碎念默認格式\n3. 只針對明顯缺漏或不通順處回查 transcript_clean.txt 對應段落；不要在本步驟做完整 transcript fidelity，嚴格忠實度比對交給 Step 07.5\n4. 確認術語翻譯一致性與段落銜接自然\n\n【Phase 2 - 影片證據圖 / GIF placement】\n1. 讀取 manifest.json，根據每張圖的 article_context 插入到文章中對應段落之後\n2. Markdown 圖片格式必須是 ![描述文字](圖片路徑)\n   ✅ 正確：![封閉迴路系統架構圖]({temp_dir}/images/frame_03.jpg)\n   ❌ 錯誤：![{temp_dir}/images/frame_03.jpg]()（路徑放在 alt text 裡是錯的！）\n3. 圖片用本地絕對路徑（如 {temp_dir}/images/frame_01.jpg）\n4. ❌ 禁止把圖片堆在文章最後面（append）——每張圖必須出現在它描述的內容附近\n5. ❌ 禁止連續兩張圖——「連續」的定義是兩張圖之間只有空白行，沒有實質文字。如果兩張圖之間沒有至少一段有意義的中文文字（不算空行），必須合併成一張或在中間加轉場說明\n6. 每篇文章至少 3 張配圖\n7. 每張圖的 alt text 要有描述性（不要寫「圖片」）\n8. ❌ 講者影像數量限制（最重要！）：\\n   - 「講者影像」= 畫面主體是講者本人、沒有投影片/圖表/文字內容的截圖（包括：純臉部特寫、講者坐在桌前說話、講者站在舞台上沒有投影片背景）\\n   - 整篇文章最多只能有 **1 張**講者影像（用於介紹講者段落）\\n   - 如果 manifest 裡有多張講者影像，只選最清晰的 1 張，其餘全部跳過\\n   - 投影片截圖背景裡有講者小窗（picture-in-picture）不算講者影像，可以正常插入\n\n【Phase 3 - 格式檢查 + 自我驗證】\n1. 用 terminal 執行 grep -o '<[^>]*>' article_draft.md 確認無 HTML tag\n2. em dash、U+2015、雙逗號與簡轉繁由 Step 08 主 Agent Final Gate 統一處理；子代理不要自行用 sed/awk 亂改，但若有改文或補圖，仍必須重新跑連續圖片檢查\n3. ⚠️ 必須執行以下自我驗證指令確認沒有連續圖片：\n   python3 -c \"\nwith open('{temp_dir}/article_draft.md') as f:\n    lines = f.readlines()\nimgs = [i for i,l in enumerate(lines) if l.strip().startswith('![')]\nfor j in range(len(imgs)-1):\n    between = lines[imgs[j]+1:imgs[j+1]]\n    if not any(l.strip() and not l.strip().startswith('![') for l in between):\n        print(f'ERROR: 連續圖片 L{imgs[j]+1} & L{imgs[j+1]+1}')\nassert all(any(l.strip() and not l.strip().startswith('![') for l in lines[imgs[j]+1:imgs[j+1]]) for j in range(len(imgs)-1)), '有連續圖片！'\nprint('OK: 無連續圖片')\n\"\n   如果驗證失敗，必須修正後重新驗證\n\n完成後用 terminal 工具寫回 {temp_dir}/article_draft.md。⚠️ 若 {temp_dir} 位於 /var/folders/ 等 macOS temp/sensitive path，禁止使用 patch/write_file 工具（會被拒絕或造成 mutation verifier 誤報）；改用 terminal 執行 Python 腳本原地讀寫，完成後用 read_file/terminal 驗證圖片數與關鍵修改確實存在。",
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
5. 進入 Step 07.6（若需要概念配圖）或 Step 08 預覽 / 交付

### Step 07.6: 可選文章概念配圖（baoyu / Codex handoff）

> 只有在使用者要求「文章配圖」「每個 H2 配圖」「幫文章做概念資訊圖」，或主 Agent 判斷文章需要概念圖提升閱讀體驗時執行。影片 evidence frames / GIF 與概念圖可以同篇共存，但必須分工清楚。

執行規則：
1. 先載入 `skill_view(name='creative/baoyu-article-illustrator')`，用文章 H2 與核心論點建立 `illustrations/outline.md` 與 `illustrations/prompts/*.md`。不要生成泛用科技場景插畫，優先 framework / comparison / flowchart / infographic。
2. 再載入 `skill_view(name='hamster-image-generation')`，依 Codex-first / contact sheet / OCR / 人眼 sanity review 的圖片 QA gate 生圖與驗圖。
3. 通過 QA 後，將概念圖插入 H2 或對應框架段落之後；證據圖仍保留在影片內容引用附近。兩種圖不要連續堆疊，中間必須有實質文字銜接。
4. 產出與回報至少包含：`illustrations/outline.md`、prompt files、生成圖、`qa-contact-sheet`、插回後的 `article_draft.md`。
5. 若 Codex / vision / OCR QA 失敗，誠實回報並保留文章文字與 evidence frames，不要改用未經使用者同意的 deterministic fallback。

**handoff contract：**
- 輸入：`article_draft.md`、H2 list、每個 H2 的核心論點、禁止泛用場景插畫。
- 輸出：`illustrations/outline.md`、`illustrations/prompts/*.md`、`illustrations/*.png`、`qa-contact-sheet`、已插入 concept figures 的文章。

### Step 08: 預覽 + 交付（🛑 強制中斷點）

> **執行前必讀**：`references/deployment-cleanup.md`
> 若本次是複用性驗證 / Dry-run，還必須先讀 `references/skill-reuse-validation.md`，並以該文件的 Final response contract 回報。

**模式分流：**
- 正式交付：先預覽 → 等待使用者確認 → 根據反饋修正 → 最後一次修改後跑 Final Gate → 使用者明確批准後才發布。
- Dry-run / 複用性驗證：不發布、不等發布批准；可以產出 contact sheet 與本地文章路徑，但必須在 final response 前跑 Final Gate，並附完整 Gate output。

**發布前公開文案清潔（重要）**：正式發布稿的前言與 frontmatter 不要保留 pipeline 內部狀態，例如「根據完整 YouTube 英文字幕整理」、「額度恢復後補跑 Gemini 視覺分析」、「僅使用非空框、非純人物截圖」或 `quality_badge: Gemini 視覺...`。這些可放在工作回報 / fidelity log，不放給一般讀者。公開前言要回答讀者進場三問，尤其說清楚「這是一部什麼影片」：節目 / 頻道、主角、訪談或報導對象，以及影片核心追問。

**預覽：**
1. 讀取 `fidelity_check.md`（Step 07.5 子代理輸出）
2. 對 nice_to_have 列表逐一判斷：必要時 `Read(transcript_clean.txt, offset=<行>, limit=<N>)` 抓對應段落，決定是否補入 article_draft.md
3. 讀取最終 `article_draft.md`
4. **穩定化預覽產物（必做）**：若工作目錄在 `/var/folders/...` 或其他 temp 路徑，先依 `references/stable-preview-artifacts.md` 將 `article_draft.md`、`contact_sheet.jpg`、`fidelity_check.md`、`notes_theme-map.md` 與 `outputs/images/` 複製到 `/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/<VIDEO_ID>/`，並把文章內圖片路徑替換成穩定目錄後，對穩定稿重跑 `final_gate.py --check-only`。Discord 預覽與後續 Notion 上傳都優先使用穩定稿，避免 temp 清理或 compaction 後圖片失效。
5. 用 Discord embed 分段預覽文章內容（每段一張卡片）
6. 用 Discord embed 預覽每張配圖（含 alt text）

**交付：**
1. 將校對後的 `article_draft.md` 與素材清單提交給使用者
   - 回報時要明確列出本輪使用過的品質流程：`hamster-writing-craft` 是否用於 Step 06/07、`fidelity_check.md` 是否完成、Final Gate 是否通過。使用者會追問「有沒有用深度解讀撰寫 skill」，不要只交檔案路徑。
   - 若文章同時含影片 evidence frames / GIF 與 baoyu concept figures，回報要分清楚兩者角色：影片截圖負責「證據」，概念圖負責「理解框架」。不要混稱為同一種配圖。
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
5. 依使用者指示發布到 Notion 時，**不要在本 Skill 複製 Notion CLI 細節**。先載入 `skill_view(name='notion-upload-workflow')`，並完全依該 Skill 的 canonical flow 執行發布與遠端驗證。本 Skill 只負責交付穩定稿路徑與 v2a 專屬注意事項：
   - 發布檔案優先使用 Step 08 產出的穩定稿（不是 `/var/folders/...` 暫存稿）
   - YouTube 來源的 `cover_image` 應使用 `analysis.json.metadata.youtube_thumbnail_url`
   - 圖片路徑可保持本地絕對路徑或穩定目錄路徑；實際 Cloudinary 上傳、URL 寫回、Notion manifest、遠端檢查以 `notion-upload-workflow` 為準
6. 複製到 Obsidian：`cp article_draft.md ~/Desktop/同步知識庫/30_Projects/倉鼠特報/發佈區/`
7. 完成後執行 `bash ${HERMES_SKILL_DIR}/scripts/cleanup_temp_dirs.sh`

> ⚠️ **注意**：`/var/folders/` 等 temp 路徑會被 `write_file` 工具拒絕。
> 寫入文章時請用 `terminal` 工具（如 `cat > article_draft.md << 'EOF'`）。

---

## Session-derived transcript-led publish lessons

- When Gemini visual analysis is blocked but captions are usable, continue as transcript-led / no-screenshot. Before publication, remove internal evidence markers such as `(transcript L...)` from the public article; keep line references only in `fidelity_check.md`.
- If the user later requests article illustrations, hand off to `creative/baoyu-article-illustrator` for H2 concept planning and `hamster-image-generation` for generation and QA. Concept figures are explanatory visuals, not video evidence.
- After inserting concept figures, run Final Gate again, then use `notion-upload-workflow`; do not publish the pre-illustration source.

## Long-video degraded visual + ASR recovery pattern

When a long YouTube video hits a provider spending cap during Gemini File API upload, preserve the downloaded `video_source.mp4` and transparently downgrade instead of pretending visual analysis succeeded. Use the reusable recipe in `references/long-video-manual-visual-and-groq-fallback.md`:

1. Record the exact provider error and mark `analysis.json` as a manual visual fallback.
2. If YouTube captions are disabled and local mlx-whisper is unavailable, extract mono low-bitrate audio, split it into bounded chunks below the transcription upload limit, transcribe each chunk with Groq, and concatenate the outputs. Treat noisy ASR as a discovery aid, not unquestioned fact.
3. Build coarse contact sheets from the original video at a fixed interval, use vision to identify non-talking-head regions, then extract representative full-resolution frames by timestamp.
4. Run a second contact-sheet QA on the candidate frames. Remove empty/loading frames, repeated frames, heavily obstructed frames, and frames whose topic cannot be visually supported. Keep only the final manifest entries used by the article.
5. In the article, distinguish claims supported by the transcript from claims personally verified in the frames. Never turn a vision model's low-resolution guess about tiny text into an exact public fact.

The fallback is still a valid evidence-bearing v2a run when the final manifest and contact-sheet QA are preserved, but the report must disclose the degraded path and its uncertainty.

## 環境需求

## References / support files
- `references/stable-preview-artifacts.md` — Stable-copy v2a deliverables from `/var/folders/...` temp workdirs into profile-owned output directories before Discord preview / Notion handoff.
- `references/sparse-visual-single-frame-and-stable-path-pitfalls.md` — Sparse visual v2a fallback: one verified frame is acceptable, manual ffmpeg manifest fallback, `/private/Users` stable-copy path bug, and post-Final-Gate over-normalization sweep.
- `references/visual-resume-after-transcript-led-draft.md` — Resume visual analysis after a transcript-led fallback once Gemini quota/billing is fixed: reuse `video_source.mp4`, manually extract assets if `extract_assets.sh` exits early, contact-sheet QA, insert evidence frames into the existing draft, then stable-copy all artifacts.
- `references/youtube-live-url-and-final-gate-normalization-pitfalls.md` — Session-derived pitfalls: normalize YouTube `/live/VIDEO_ID` URLs to canonical `/watch?v=VIDEO_ID`, sanity-check zhtw/OpenCC over-normalization after Final Gate, and stable-copy transcript-led no-image artifacts.
- `references/local-video-visual-retry-and-manual-assets.md` — Local-file v2a resume pattern after Gemini quota is raised; includes Python/env selection fix, manual ffmpeg frame/GIF extraction, compatible manifest writing, and >4-image contact sheet QA pitfall.
- `references/static-slide-minimal-asset-fallback.md` — When Gemini finds only a static title slide and `extract_assets.sh` fails early, use direct ffmpeg extraction + compatible manifest + QA instead of blocking the article or inventing additional frames.
- `references/video-analyzer-readback-and-provider-fallback.md` — provider/model 404 handling, mandatory `analysis.json` readback, and embedded-X-video writing handoff split.
- `references/x-embedded-video-v2a.md` — X status with embedded video: convert via baoyu-danger-x-to-markdown, use downloaded MP4 + ASR, separate video evidence from X longform reconstruction, and handle manual asset fallback/stable preview paths.
- `references/gemini-cap-text-only-fallback.md` — Gemini monthly spending-cap fallback: continue as a transparent transcript-led deep reading when captions are usable, with no evidence frames or unverified visual claims.
- `references/visual-resume-after-transcript-led-draft.md` — When quota/billing is fixed after a transcript-led fallback, resume visual analysis without rewriting: reuse local `video_source.mp4`, filter assets via contact-sheet QA, insert verified evidence into the existing draft, and stable-copy the image paths.
- `references/transcript-led-concept-figure-handoff.md` — When Gemini visual analysis is blocked but the user requested article 配圖: keep evidence frames blocked, but allow baoyu / Codex concept figures with contact-sheet QA and clear reporting.
- `references/transcript-led-local-ai-concept-figures-publish-2026-06-28.md` — Concrete transcript-led v2a session: Gemini spending-cap upload blocker, concept-figure handoff, Codex batch hang salvage, Notion publish verification, and topic-specific OpenCC drift (`本地 AI` → `本機 AI`) scan.
- `references/local-mp4-transcript-led-asr.md` — Local MP4 fallback: when Gemini visual analysis is blocked and there is no YouTube caption path, extract 16k mono audio, transcribe via Groq with the correct language, normalize ASR product-name errors, and continue as no-image transcript-led v2a.
- `references/transcript-led-code-with-claude-series-example.md` — Concrete session note for a long podcast run: how to mark visual steps blocked, convert Step 07 into editorial review, preserve transparency, and handle Final Gate after normalization fails on zh-en spacing.
- `references/transcript-led-code-with-claude-series-example.md` — Concrete session note for a long podcast run: how to mark visual steps blocked, convert Step 07 into editorial review, preserve transparency, and handle Final Gate after normalization fails on zh-en spacing.
- `references/transcript-led-invalid-visual-qc.md` — Visual extraction/QC fallback when Gemini/extractor produces zero usable assets or mismatched frames: cancel Step 03, continue transcript-led, prohibit visual claims/placeholders, and avoid inventing key frames to satisfy extractor scripts.
- `references/transcript-led-draft-plus-figure-brief.md` — 輕量模式：已有 transcript、使用者只要繁中深度解讀初稿與配圖方案時，產出 article / figure brief / fidelity 三檔，並明確標示未跑視覺分析與未插入真實截圖。
- `references/transcript-led-speech-and-subtitle-validation.md` — 演講／keynote 明確免視覺分析時的 transcript-led 分流，以及字幕覆蓋率、人工／自動字幕來源與 rolling-caption 重複驗證。
- `references/conference-series-batch-deep-reading.md` — 大會 / 活動系列影片批次深度解讀：manifest-first、sub-agent 分批寫作、主 agent text QC + image QA 雙 gate、未通過圖片 QA 時禁止發布。
- `references/conference-batch-existing-article-review.md` — 已完成大會系列文章的 transcript 對照 review 模式：不重寫不發布，輸出逐篇 deep-reading / terminology review artifact 與 batch summary。
- `references/conference-batch-text-artifact-gates.md` — 大會批次的 transcript-led 文字包檢查：article / figure brief / fidelity 三件套、概念圖 brief 規格、證據表與 batch validator gates。
- `references/code-with-claude-transcript-led-batch-notes.md` — Code with Claude 系列 transcript-led 批次補充：ASR 將 Claude 誤轉 Cloud 的透明處理、三件套 gate、frontmatter divider validator 坑與最小 patch loop。
- `references/code-with-claude-series-24-artifact-validation.md` — Code with Claude #24 三件套實例補充：manifest path resolution、strict validator 下 support artifacts 避免 H1、hamster_note 單獨補長、fidelity disclosure。
- `references/code-with-claude-existing-article-review-09-16.md` — Code with Claude 09–16 既有文章 review 實例：逐篇 deep-reading + terminology artifacts、batch summary 統計、range 續作與 vision/現況邊界注意事項。
- `references/code-with-claude-existing-article-review-17-24.md` — Code with Claude 17–24 既有文章 review 實例：HeroGen 85% success-rate 分母修正、Spotify retranscript fallback、Microsoft Foundry/Claude Code Routines/Auto mode 術語白話化與 batch summary conventions。
- `references/skill-repo-collaboration-and-update.md` — 維護本 skill repo 時的 upstream/fork/collaborator 檢查流程：先確認 Hermes 實際載入的本機路徑、canonical remote、fork remote、ahead/behind、PR 是否已合併，以及 dry-run push 的實際 GitHub 權限。

## 環境需求
## Session-derived lessons: split-video Gemini retry and full evidence index (2026-07-19)

### Gemini model selection must follow the actual analyzer script

Before running a retry, inspect `video_analyzer.py`'s `DEFAULT_MODEL` and use the current script default unless there is a documented reason to override it. The current analyzer default is `gemini-3-flash-preview`; older fallback text that hardcodes `gemini-2.5-flash` is stale and must not silently override the script. If a user raises the Gemini spending cap after a 429 upload failure, report the model choice transparently and do not claim that an older fallback is current.

### Long-video visual retry: split, analyze, merge

When a long YouTube video upload hits a project spending cap or processing risk, reuse the already downloaded local `video_source.mp4`. Split it into approximately 60-minute, audio-free parts, analyze each part with the current Gemini Flash model, then merge `key_frames` and `gif_segments` by adding the part offset to every timestamp in the later segment. Preserve `source_part` and `timestamp_seconds` in the merged manifest so every evidence frame remains auditable. Extract final images from the original full-resolution video, not from the reduced analysis proxy or split preview files.

### Evidence-frame QA and exhaustive reference mode

After Gemini returns frames, create a contact sheet and have the main agent perform its own visual QA. Remove pure talking-head, loading, black-player, transition, blurry, obstructed, and near-duplicate frames. If the user explicitly wants every captured screen for UI reference, do not reduce the article to only the editorial highlight set: append a dedicated `## 影片系統畫面索引` section containing every retained Gemini key frame and GIF, each followed by a one-line `圖：...` caption. Captions keep the parser from treating images as continuous blocks and make the index usable as a UI reference appendix.

### Notion handoff after exhaustive media insertion

A large exhaustive index can produce dozens of media blocks. Run `preflight --file ... --json` and verify the local image count before publishing. After publish, use the same page ID for any correction; `images_uploaded: 0` on a later update is expected once Markdown already contains Cloudinary URLs. Always run `inspect` and a Notion blocks readback to verify block count, image-block count, first/last text, and remote terminology.

## 環境需求

| 類型 | 需求 |
|------|------|
| 系統工具 | `yt-dlp`, `ffmpeg`, `ffprobe` |
| Python | `python3` + `google-genai` |
| 環境變數 | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` |
