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

### ⚠️ Context Compaction 恢復規則

如果你看到 `[CONTEXT COMPACTION]` 訊息，代表之前的對話被壓縮了。**必須立即執行以下恢復動作**：

1. **重讀本 Skill**：`skill_view(name='video-to-article')` — 重新載入完整規則
2. **列出待完成步驟**：根據壓縮摘要中的進度，列出 Step 01-08 中尚未完成的步驟
3. **確認工作目錄**：`ls {temp_dir}/` 確認已有的產出物
4. **從斷點繼續**：不要重做已完成的步驟

---

## 工作流（8 步）

| Step | 職責 | 執行者 | 參考文件 | 輸入 | 輸出 |
|------|------|--------|---------|------|------|
| 01 | 環境初始化 | 腳本 | — | 使用者觸發 | `{temp_dir}/` |
| 02 | Gemini 視覺分析 | 腳本 | — | 影片來源 | `analysis.json` |
| 03 | 素材擷取 | 腳本 | — | analysis.json + 影片 | `images/` + `manifest.json` |
| 04 | 字幕獲取清理 | 主Agent | `references/workflow-technical.md`, `references/fallbacks.md` | 影片 URL | `transcript_clean.txt` |
| 05 | 主題地圖萃取 | 主Agent | — | 字幕 + analysis.json | `notes_theme-map.md` |
| 06 | 草稿撰寫 | 主Agent | `references/output-format.md` | 主題地圖 + manifest | `article_draft.md`（純文字） |
| 07 | 審校配圖 | **子代理** | `references/output-format.md` | 草稿 + 字幕 + manifest | `article_draft.md`（含圖） |
| 08 | 預覽 + Final Gate + 交付 | 主Agent | `references/deployment-cleanup.md`, dry-run 時加讀 `references/skill-reuse-validation.md` | 完成的文章 | 預覽 / Gate output / Notion 頁面（需使用者確認後） |

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

**影片路徑：** `analysis.json` 的 `metadata.local_video_path` 包含已下載影片的本地路徑。`extract_assets.sh` 應使用此路徑，**不要重新下載影片**。

**品質檢查（必做，不可跳過）：**

⚠️ **Vision 回覆長度限制**：所有 `vision_analyze` 的 `question` 參數必須以「回答限 1-2 句話」結尾。
長篇 vision 回覆會撐爆 context window。

素材擷取完成後，執行以下檢查流程：

1. **Contact sheet 快篩**：用 `vision_analyze` 看 contact sheet，question 寫：「這 9 張縮圖中，哪幾張是純講者畫面（沒有投影片）？哪幾張有模糊？回答限 1-2 句話，只列編號。」
2. **逐張深檢**：對所有 `importance: high` 的 key_frame，**逐張** `vision_analyze` 確認，question 寫：「這張截圖文字是否清晰可讀、無模糊殘影？投影片是否完整展開？回答限 1 句：OK 或描述問題。」
3. **GIF 首尾幀檢查**：`vision_analyze` 不支援 `.gif` 檔案；每個 GIF 必須擷取**初始幀與最後一幀**各看一次，question 寫：「這是 GIF 的首/尾幀。畫面是否有實質內容（非黑屏/logo）？回答限 1 句。」
4. **修復流程**：發現問題幀時，用 ffmpeg 在 ±1~2 秒範圍嘗試多個時間點，再次 `vision_analyze` 選最清晰的替換

⚠️ 「只看 contact sheet」不夠！縮圖太小看不出文字模糊，必須逐張檢查 high importance 幀。

GIF 首尾幀擷取範例：
```bash
gif="images/gif_01_02_07-02_17.gif"
frames=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 "$gif")
last=$((frames - 1))
ffmpeg -y -i "$gif" -vf "select='eq(n,0)'" -frames:v 1 /tmp/gif_first.jpg
ffmpeg -y -i "$gif" -vf "select='eq(n,'"$last"')'" -frames:v 1 /tmp/gif_last.jpg
# 然後分別用 vision_analyze 看 /tmp/gif_first.jpg 與 /tmp/gif_last.jpg
```

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

### Step 07: 審校配圖（delegate_task 子代理）

> ⚠️ **本步驟使用 `delegate_task` 派子代理執行**，不要自己做。
> 子代理有乾淨的 context，不會受到前面步驟的資訊干擾。

用以下模板呼叫 `delegate_task`（將 `{temp_dir}` 替換為實際工作目錄）：

```
delegate_task(
  goal="審校並配圖 video-to-article 文章草稿",
  context="工作目錄: {temp_dir}\n\n要讀取的檔案:\n- {temp_dir}/article_draft.md（純文字草稿）\n- {temp_dir}/transcript_clean.txt（原始字幕）\n- {temp_dir}/manifest.json（圖片索引，每張圖有 article_context 描述對應段落）\n\n寫作規範（先載入再開始工作）:\n1. skill_view(name='video-to-article', file_path='references/output-format.md') — 格式規範\n2. skill_view(name='hamster-content-analysis') — 倉鼠寫作方法論（Opening Hook、論證框架等）\n\n任務（依序執行）:\n\n【Phase 1 - 內容校對 + 寫作優化】\n1. 讀取 transcript_clean.txt，逐段比對 article_draft.md\n2. 補漏遺漏的：重要論點、數據、具體案例、轉化邏輯\n3. 將遺漏內容融入文章對應段落（不是列清單）\n4. 按 hamster-content-analysis 的寫作方法論優化文章結構和表達\n5. 確認術語翻譯一致性\n\n【Phase 2 - 配圖】\n1. 讀取 manifest.json，根據每張圖的 article_context 插入到文章中對應段落之後\n2. Markdown 圖片格式必須是 ![描述文字](圖片路徑)\n   ✅ 正確：![封閉迴路系統架構圖]({temp_dir}/images/frame_03.jpg)\n   ❌ 錯誤：![{temp_dir}/images/frame_03.jpg]()（路徑放在 alt text 裡是錯的！）\n3. 圖片用本地絕對路徑（如 {temp_dir}/images/frame_01.jpg）\n4. ❌ 禁止把圖片堆在文章最後面（append）——每張圖必須出現在它描述的內容附近\n5. ❌ 禁止連續兩張圖——「連續」的定義是兩張圖之間只有空白行，沒有實質文字。如果兩張圖之間沒有至少一段有意義的中文文字（不算空行），必須合併成一張或在中間加轉場說明\n6. 每篇文章至少 3 張配圖\n7. 每張圖的 alt text 要有描述性（不要寫「圖片」）\n8. ❌ 講者影像數量限制（最重要！）：\\n   - 「講者影像」= 畫面主體是講者本人、沒有投影片/圖表/文字內容的截圖（包括：純臉部特寫、講者坐在桌前說話、講者站在舞台上沒有投影片背景）\\n   - 整篇文章最多只能有 **1 張**講者影像（用於介紹講者段落）\\n   - 如果 manifest 裡有多張講者影像，只選最清晰的 1 張，其餘全部跳過\\n   - 投影片截圖背景裡有講者小窗（picture-in-picture）不算講者影像，可以正常插入\n\n【Phase 3 - 格式檢查 + 自我驗證】\n1. 用 terminal 執行 grep -o '<[^>]*>' article_draft.md 確認無 HTML tag\n2. em dash、U+2015、雙逗號與簡轉繁由 Step 08 主 Agent Final Gate 統一處理；子代理不要自行用 sed/awk 亂改，但若有改文或補圖，仍必須重新跑連續圖片檢查\n3. ⚠️ 必須執行以下自我驗證指令確認沒有連續圖片：\n   python3 -c \"\nwith open('{temp_dir}/article_draft.md') as f:\n    lines = f.readlines()\nimgs = [i for i,l in enumerate(lines) if l.strip().startswith('![')]\nfor j in range(len(imgs)-1):\n    between = lines[imgs[j]+1:imgs[j+1]]\n    if not any(l.strip() and not l.strip().startswith('![') for l in between):\n        print(f'ERROR: 連續圖片 L{imgs[j]+1} & L{imgs[j+1]+1}')\nassert all(any(l.strip() and not l.strip().startswith('![') for l in lines[imgs[j]+1:imgs[j+1]]) for j in range(len(imgs)-1)), '有連續圖片！'\nprint('OK: 無連續圖片')\n\"\n   如果驗證失敗，必須修正後重新驗證\n\n完成後用 terminal 工具寫回 {temp_dir}/article_draft.md",
  toolsets=["terminal", "file", "skills", "vision"]
)
```

**子代理完成後**，主 Agent 讀取 `article_draft.md` 確認圖片已正確嵌入，然後進入 Step 08。

### Step 08: 預覽 + 交付（🛑 強制中斷點）

> **執行前必讀**：`references/deployment-cleanup.md`
> 若本次是複用性驗證 / Dry-run，還必須先讀 `references/skill-reuse-validation.md`，並以該文件的 Final response contract 回報。

**模式分流：**
- 正式交付：先預覽 → 等待使用者確認 → 根據反饋修正 → 最後一次修改後跑 Final Gate → 使用者明確批准後才發布。
- Dry-run / 複用性驗證：不發布、不等發布批准；可以產出 contact sheet 與本地文章路徑，但必須在 final response 前跑 Final Gate，並附完整 Gate output。

**預覽：**
1. 讀取子代理完成的 `article_draft.md`
2. 用 Discord embed 分段預覽文章內容（每段一張卡片）
3. 用 Discord embed 預覽每張配圖（含 alt text）

**交付：**
1. 將校對後的 `article_draft.md` 與素材清單提交給使用者
2. **在此停下，等待使用者回覆**
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
   # ✅ 只需兩個參數！frontmatter 中的 tags/url/note/cover 會自動讀取
   # ❌ 不要再手動傳 --tags --url --note --image，那些已在 frontmatter 裡
   # ⭐ cover_image：YouTube 影片直接用 analysis.json 裡的 youtube_thumbnail_url
   # ⚠️ 圖片路徑保持本地路徑！腳本自動上傳 Cloudinary 並替換
   python3 ~/.hermes/skills/openclaw-imports/circleghost-content-hamster-reporting/scripts/python/notion_hamster_push.py \
     --title "文章標題" --file article_draft.md
   ```
   推送成功後會自動生成 `notion_manifest.json`（image→block_id 映射）。

   **修復圖片/更新文章**：用 `--update` 模式重新推送整篇文章：
   ```bash
   python3 ~/.hermes/skills/openclaw-imports/circleghost-content-hamster-reporting/scripts/python/notion_hamster_push.py \
     --title "文章標題" --file article_draft.md --update <PAGE_ID>
   ```

6. 複製到 Obsidian：`cp article_draft.md ~/Desktop/同步知識庫/30_Projects/倉鼠特報/發佈區/`
7. 完成後執行 `bash ${HERMES_SKILL_DIR}/scripts/cleanup_temp_dirs.sh`

> ⚠️ **注意**：`/var/folders/` 等 temp 路徑會被 `write_file` 工具拒絕。
> 寫入文章時請用 `terminal` 工具（如 `cat > article_draft.md << 'EOF'`）。

---

## 環境需求

| 類型 | 需求 |
|------|------|
| 系統工具 | `yt-dlp`, `ffmpeg`, `ffprobe` |
| Python | `python3` + `google-genai` |
| 環境變數 | `GEMINI_API_KEY` 或 `GOOGLE_API_KEY` |
