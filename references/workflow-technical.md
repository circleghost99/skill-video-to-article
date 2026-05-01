# Technical Workflow Reference

這份文件定義 `video-to-article` v1 的技術主流程。

## v1 技術定位

v1 先支援：
- **單支 YouTube**
- **字幕可取得**
- **字幕驅動的文章化流程**

不要把這份流程當成多平台、多影片、無字幕 ASR pipeline。

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

**首選：`youtube-transcript-api`（繞過 yt-dlp 429 / impersonate 限制）**

```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
transcript_list = api.list(video_id='VIDEO_ID')
for t in transcript_list:
    if t.language_code == 'zh':  # 或其他目標語言
        segs = t.fetch()
        data = [{'start': s.start, 'duration': s.duration, 'text': s.text} for s in segs]
```

**次選：`yt-dlp`（若 youtube-transcript-api 失敗）**

下載字幕時，語言代碼必須符合 YouTube 的「翻譯字幕格式」。

**語言代碼格式：** `目標語言-來源語言`
- 例如 `zh-Hans-zh` = Chinese (Simplified) from Chinese（即中文原生的 auto caption）
- 例如 `en-zh` = English from Chinese（即中文影片被翻譯成英文的 auto caption）

**標準下載命令（適用於多數中文 / 英文影片）：**
```bash
yt-dlp --write-subs --write-auto-subs \
  --sub-langs zh-Hans-zh,zh-Hant-zh,en-zh,en \
  --skip-download -o "$DEST/subs.%(ext)s" "$URL"
```

**若上述命令顯示「no subtitles for the requested languages」：**
1. 先用 `yt-dlp --list-subs "$URL"` 查看該影片真實的字幕代碼
2. 確認是「翻譯字幕格式」還是「原生字幕格式」
3. 替換 `--sub-langs` 參數後重試

**若遇到 429 Too Many Requests：**
- 依 `references/fallbacks.md` 的 429 處理章節處理（先試 youtube-transcript-api，再退避重試）

**保存原則：**
字幕資料保存為 JSON：
- `transcript_raw.json`（含時間軸）

清理後保存為：
- `transcript_clean.txt`（純文字，去時間碼，合併短句）

**當完全無法取得字幕時：**
若 YouTube 原生無任何字幕，且 `youtube-transcript-api` 與 `yt-dlp` 均失敗：
1. **停止執行**：不可假造字幕或用 LLM 幻想內容。
2. 通知使用者：「這支影片沒有可用字幕，請提供 transcript 檔案，或更換其他有字幕的影片。」
3. 根據使用者回覆，決定是否中斷任務或手動載入外部 transcript。

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
- 沒有任何可用字幕
- auto captions 噪音高到無法判讀主張
- 影片本身資訊密度過低

遇到這些情況，交給 `references/fallbacks.md` 決定是降級還是停下。
