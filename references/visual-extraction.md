# Visual Extraction Reference

Use this reference when extracting frames, screenshots, and GIFs from a source video.

## ⚠️ Step 0 — Pre-flight Check（MUST RUN FIRST）

**在任何 ffmpeg 操作之前，必須執行以下檢查：**

影片路徑應從 workflow context 取得（通常是 `$TEMP_DIR/VIDEO.mp4`），不要硬編碼。

```bash
# 動態取得影片路徑（由 workflow 提供）
VIDEO_PATH="${1:-$TEMP_DIR/VIDEO.mp4}"

# Step 0.1: 檢查影片檔是否存在
if [ ! -f "$VIDEO_PATH" ]; then
    echo "ERROR: Video file not found at $VIDEO_PATH"
    exit 1
fi

# Step 0.2: 用 ffprobe 驗證影片是否可讀（這是關鍵！）
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$VIDEO_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: ffprobe failed — video file is corrupt or unreadable"
    exit 2
fi

# Step 0.3: 驗證視頻串流存在
ffprobe -v error -select_streams v:0 -show_entries stream=codec_type,width,height -of csv=s=x:p=0 "$VIDEO_PATH"
if [ $? -ne 0 ]; then
    echo "ERROR: no video stream found"
    exit 3
fi
```

**失敗時的 Fallback 順序（按順序嘗試）：**

| 優先順序 | 來源 | 操作 |
|---------|------|------|
| 1 | 來源 URL 直接下載 | `yt-dlp -f bestvideo[ext=mp4] <url> -o /tmp/video.mp4` |
| 2 | Browser capture | 使用 canvas tool 或手動截圖 |
| 3 | YouTube transcript page | `web_fetch` 取得章節時間戳，用章節描述代替視覺 |

**⚠️ 注意**：如果 Step 0 失敗，**不要跳過截圖流程**。嘗試 Fallback 1-3，仍失敗才放棄視覺資產，並在文章中標註「本文章無視覺輔助素材」。

---

## Goal

Capture only visuals that add explanatory value to the article. Do not create screenshots or GIFs just because the workflow can.

## Selection rules

Prefer screenshots when a single frame communicates the key point:
- static slides
- architecture diagrams
- dashboards without meaningful motion
- code or UI states that do not depend on transition

Prefer GIFs when motion is the point:
- terminal execution flow
- UI state transitions
- progress indicators
- before/after interactions
- scrolling sequences where order matters

## Density heuristics

Adjust asset count to the material:
- Talking-head / interview / podcast: usually 4-6 screenshots, 0-1 GIF
- Product demo / UI walkthrough: usually 6-12 screenshots, 1-3 GIFs
- Slide-heavy technical talk: usually 8-15 screenshots, 0-2 GIFs

Do not treat these as quotas. Treat them as sanity ranges.

## Frame exploration

Use a two-pass approach: quick exploration first, then adaptive extraction.

### Pass 1 — Exploration（低成本偵測）

Goal: determine the video's content type and duration.

**⚠️ 重要：不要只取樣片頭。**  
許多「系統解說」類影片的開頭是講者在說話（30-60秒），但後面會大量展示 UI 畫面。只看片頭會錯誤分類成 talking-head，導致 fps 過低、錯過關鍵截圖。

**取樣策略：必須覆蓋至少 3 個時間段**

1. Get video duration: `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /tmp/video.mp4`
2. Extract sparse sample frames across the full video — do NOT cluster at the beginning:
   - 範例（5-6 分鐘影片）：取 frame at 0s, 30s, 60s, 90s, 150s, 210s, 270s, 330s
   - 範例（10+ 分鐘影片）：取 frame at 0s, 60s, 120s, 180s, 240s, 300s
3. Use vision to classify ALL sampled frames:

| Content type | 特征 |
|-------------|------|
| **Talking-head / 訪談** | 單人／雙人說話為主，背景固定，**全片**極少螢幕共享 |
| **教學簡報** | 有大量 PPT、slide、螢幕錄製 |
| **操作示範** | UI 操作、終端機執行、軟體 demo；**或：影片中後段有大量 UI 螢幕** |
| **會議記錄** | 多與會者、討論記錄、白板 |

> **分類修正規則**：如果任何一個取樣幀包含 UI 畫面（軟體介面、網頁、終端機、Obsidian、Notion 等），就將影片分類為「操作示範」，並套用 ×1.0 multiplier。不要被片頭的 talking-head 誤導。

4. Classify content density:
   - **低密度**：談話為主，圖表少 → 少量截圖，0-1 GIF
   - **高密度**：PPT、程式操作、圖表多 → 大量截圖，2-4 GIF

### Pass 2 — Adaptive Extraction（根據偵測結果調整）

**Duration-based frame rate（先看時長）：**

| 影片時長 | 探索取樣頻率 | 說明 |
|---------|------------|------|
| **< 30 分鐘** | `fps=1`（每秒 1 幀） | 資訊密度高，幾乎不漏東西 |
| **30 分鐘 – 60 分鐘** | `fps=1/3`（每 3 秒 1 幀） | 平衡資訊量與檔案大小 |
| **> 60 分鐘** | `fps=1/5`（每 5 秒 1 幀） | 太長了，精準取樣會爆炸，5 秒一幀是甜點 |

**Content-type multiplier（再乘以內容密度）：**

| 內容類型 | frame 取樣率加成 |
|---------|----------------|
| Talking-head / 訪談 | × 0.5（不需要那麼密） |
| 操作示範 | × 1.0（標準） |
| 教學簡報 | × 1.5（每張 slide 幾乎都要） |
| 混合（會議） | × 1.0（標準） |

**Examples:**
```bash
# 30分鐘教學簡報 → 每3秒×1.5 ≈ 每2秒
ffmpeg -i /tmp/video.mp4 -vf fps=1/2 /tmp/explore/frame_%04d.jpg

# 90分鐘訪談 → 每5秒×0.5 ≈ 每10秒
ffmpeg -i /tmp/video.mp4 -vf fps=1/10 /tmp/explore/frame_%04d.jpg

# 20分鐘操作示範 → 每1秒×1.0 = 每秒1幀
ffmpeg -i /tmp/video.mp4 -vf fps=1 /tmp/explore/frame_%04d.jpg
```

After exploration, use vision to identify high-value frames, then do formal extraction at those precise timestamps.

**Pass 2 完成標準（強制）**：
- 根據 Pass 1 的探索結果，選擇**至少 3-5 個高價值時間點**
- 每個時間點執行正式截圖或 GIF extraction
- 截圖必須與文章相對應，不能是「感覺有就好」
- 視覺資產數量參考密度表：
  - Talking-head / 訪談：4-6 張截圖，0-1 GIF
  - 教學簡報：8-15 張截圖，0-2 GIF
  - 操作示範：6-12 張截圖，1-3 GIF
- **沒有完成 Pass 2 就不能進入寫文章階段**

### 機制錨點（Mechanism Anchors）

對於 OpenClaw 這類「系統解說」類影片，以下時間點或畫面提到具體 UI 元件，應優先截圖：

| 畫面 | 為什麼要截 |
|------|-----------|
| Main Intake 頁面 | 看到 Task/Decision/Material 的第一次分流視覺 |
| Distillation Queue 審批區 | 四個按鈕（同意/合併/升級/丟掉）具體呈現 |
| Skill Pack 頁面 | 養成的 Skills 長什麼樣 |
| 河馬桌寵（張嘴 vs 閉嘴）| 兩個狀態的對照 |

這些畫面是「機制鏈條」的視覺化，截圖能幫讀者快速理解系統的運作方式。

### Benchmark 參照幀（影片：N519Nj7LRXA）

以下是本 skill 實測時從这支 OpenClaw 系統解說影片中提取的關鍵截圖，已保存於 `references/anchors/` 目錄，可作為「合格截圖」的參照標準：

| 幀 | 秒數 | 畫面描述 | 對應文章段落 |
|----|------|---------|-----------|
| frame_3s.jpg | ~3s | 2ndSelf Obsidian 介面（腳本、頻道流量清單）| 系統入口 |
| frame_61s.jpg | ~61s | Welcome 頁（Main Intake、Main Work Surface 結構）| 系統架構 |
| frame_91s.jpg | ~91s | Main Intake 全頁（Tasks/Decisions/Research Materials 分類）| Intake 分流 |
| frame_121s.jpg | ~121s | 左側資料夾導航（00 Inbox, 10 Decisions...）| 正式沉澱 |
| frame_151s.jpg | ~151s | Thesis Candidates 頁（Confidence、Summary 欄位）| Distillation Queue |
| frame_211s.jpg | ~211s | Skill Pack（Content Blueprint，穩定度 0.98）| Skill 升級 |
| frame_271s.jpg | ~271s | GitHub 安裝說明（macOS Full vs Linux Core）| 平台限制 |
| frame_301s.jpg | ~301s | Custom Prompt 段落（5 件事定制框架）| 客製化 |

> **取樣教訓**：這支片片頭是講者在說話（前 30 秒），容易被錯誤分類為 talking-head。但 30 秒後出現大量 UI 畫面。正確做法是：**Pass 1 取樣時從頭到尾分散取樣，不要只取片頭**。

## Browser capture is not the default

Do not default to opening the video in a browser and manually screenshotting frames.

Browser capture is only a fallback when:
- the source is gated behind authenticated playback
- direct file access is unavailable
- the page itself contains critical context outside the raw video frames

If a local video file is available, use ffmpeg-based extraction instead.

## Formal extraction

Examples:
```bash
# screenshot
ffmpeg -ss <TIME> -i /tmp/video.mp4 -vframes 1 -q:v 2 output.jpg

# GIF
ffmpeg -ss <TIME> -t 5 -i /tmp/video.mp4 \
  -filter_complex "[0:v] fps=15,scale=800:-1,split [a][b];[a] palettegen [p];[b][p] paletteuse" \
  output.gif
```

## Review questions

Before finalizing assets, check:
- Does each image or GIF explain something the article discusses nearby?
- Is any GIF replaceable with a screenshot?
- Is any paragraph describing a visual that should actually be shown?
- Are there too many near-duplicate screenshots?

## 整合 baoyu-article-illustrator（圖文整合）

當影片本身視覺素材不足（talking-head、訪談）時，在 Pass 2 完成後，主動將文章交給 `baoyu-article-illustrator` skill 處理圖文整合。

### 觸發條件（滿足任一即觸發）

| 條件 | 說明 |
|------|------|
| **來源截圖數 < 密度表下限** | 如 talking-head < 4 張、教學簡報 < 8 張、操作示範 < 6 張 |
| 影片類型為 talking-head / 訪談 | 預期視覺素材稀少，即便截圖達標也主動補 AI 圖提升質感 |
| 使用者明確指定 | 「需要 AI 生圖輔助」 |

### 密度計算範圍（重要）

計算密度時，**必須包含以下所有来源**：
1. 本次 Pass 2 新提取的截圖
2. `references/anchors/` 中預存的 benchmark frames（如本 skill 已收錄的 N519Nj7LRXA 的 8 張參考圖）
3. 任何已存在於 `outputs/images/` 的相關圖片

**總計 < 密度下限時，觸發 baoyu。**

### 整合流程

不需要開 sub-agent。在同一個倉鼠 session 裡，依序執行：

```
Step 1：完成 video-to-article 文章草稿
         ↓
Step 2：切換到 baoyu-article-illustrator 的流程
         ↓
Step 3：讀取 baoyu SKILL.md 與 references
         ↓
Step 4：分析文章結構與視覺缺口
         ↓
Step 5：若已有來源截圖 / frame，複製到 references/ 作為參考圖
         ↓
Step 6：生成 prompt 並執行圖片生成
         ↓
Step 7：圖文整合進文章
         ↓
Step 8：完成交付
```

### 與 baoyu 的協作重點

1. **Frame 當參考圖**：把高價值的 frame 圖片當作 baoyu 的 reference image，baoyu 會自動分析並決定用 `direct` / `style` / `palette`
2. **不用預先決定誰用誰不用**：把 frame 和文章一起交給 baoyu，讓它根據文章結構決定
3. **風格設定**：如果倉鼠知道使用者偏好（從 prior 任務或使用者反饋累積），可以在 Step 3 預設 type/style，跳過互動式問答
4. **倉鼠 mascot**：baoyu 預設會在每張圖的角落放知識倉鼠 mascot，這是品牌元素，不應移除

### 觸發時的標準話語

在交付給 baoyu 之前，倉鼠應主動說：
>「這部影片屬於 talking-head 類型，來源截圖 {N} 張，低於密度表下限。我將把文章交給 baoyu-article-illustrator 處理圖文整合。」

### 不需要整合 baoyu 的情況

- 來源截圖已達密度表標準（如簡報教學 8-15 張圖）
- 使用者明確說「不需要 AI 生圖」
- 影片本身畫面豐富，已完成充分視覺探索

