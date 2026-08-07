# YouTube v1 Fallbacks & Downgrade Rules

> **坑點記錄（2026-05-17）**
> - `final_gate.py` 的 `find_body_dividers()` 把 `---` 的允許位置鎖定在「frontmatter 結尾 + body 第一行」。body 中間的 `---`（如分隔正文與倉鼠碎碎念）會觸發 false positive。
> - **解法**：正文內部分隔改用 `***`（三個星號）或直接刪除分隔線（倉鼠碎碎念本身就是一個明確的 `## H2` 標記，視覺分隔多餘）。日後若 `find_body_dividers` 的 allow-list 擴展至支援 body 中間的 `---`，即可恢復。

這份文件只處理 `video-to-article` v1 的 fallback。

v1 原則：**先把有字幕單片做好。**
Fallback 是保護欄，不是主舞台。

## 1. 字幕品質分級

### 🟢 Manual Subtitle
- 有人工字幕
- 可直接進入清理與文章化流程

### 🟡 Usable Auto Caption
- 只有 YouTube automatic captions
- 但主要名詞、句意、段落仍可辨識
- 需要先做清理，才能進文章流程

### 🔴 Unusable / No Caption
- 沒字幕
- 或字幕破碎到無法辨識主張與例子
- **v1 不主打這種情境**

## 2. v1 的處理規則

### Scenario: Manual Subtitle Available
- 正常走主流程
- 品質標記可用：`🟢 Full Grade`

### Scenario: Only Auto Caption Available but Readable
- 先做字幕清理
- 交付時明講：字幕來自 auto captions，可能有輕微術語誤差
- 品質標記可用：`🟡 Caption-Cleaned`

### Scenario: No Caption or Caption Unusable
- 不要硬做完整文章
- 直接停下，請使用者：
  - 換一支有字幕的影片，或
  - 提供 transcript
- 若使用者仍只想要粗整理，才能降級成簡短 skeleton note
- 品質標記可用：`🔴 Skeleton Only`

## 3. 資訊密度過低

若影片大量是：
- 寒暄
- 贊助段
- 訂閱提醒
- 重複鋪陳

處理方式：
- 強力修剪噪音
- 保留核心觀點
- 不要為了篇幅硬撐成長文

可以改交付為：
- 短篇解讀文
- 或 deep note

## 4. 視覺稀疏

如果影片幾乎沒有有價值畫面：
- 不要硬做多張截圖
- 交付重點放在文章本身
- 可附註：`本片以口語說明為主，視覺資訊有限，因此以文字解讀為主。`

## 5. 429 Too Many Requests 處理（yt-dlp）

當 `yt-dlp` 回應 429 或 423（rate limit / blocked）時：

1. **立即切換到 429-safe 字幕流程**：語言白名單（不要 `--sub-langs all`）、請求前 sleep 60 秒、批次切分與快取
2. `youtube-transcript-api` 也可能被字幕端點限流；使用前同樣 sleep/backoff，不要裸呼叫批次 API
3. **退避重試**：等待 60-120 秒，以指數退避重試，最多 3 次
4. 仍失敗 → 停下，回報使用者

### `youtube-transcript-api` 使用方式

```bash
python3 -m pip install youtube-transcript-api --break-system-packages
```

```python
import time
from youtube_transcript_api import YouTubeTranscriptApi

# 429-safe: request a small language whitelist, sleep before subtitle endpoint calls,
# and retry 429 with backoff instead of tight loops.
time.sleep(60)
api = YouTubeTranscriptApi()
transcript_list = api.list(video_id='VIDEO_ID')
for t in transcript_list:
    if t.language_code in {'zh-TW', 'zh-Hant', 'en'}:
        time.sleep(60)
        segs = t.fetch()
        data = [{'start': s.start, 'duration': s.duration, 'text': s.text} for s in segs]
        break
```

**範例退避 script（yt-dlp fallback）：**
```bash
RETRY=0
MAX_RETRIES=3
until yt-dlp --write-subs --write-auto-subs --sub-langs "zh-TW,en" \
  --sleep-interval 5 --max-sleep-interval 10 --sleep-subtitles 60 --retries 10 "$URL"; do
  RETRY=$((RETRY + 1))
  if [ $RETRY -ge $MAX_RETRIES ]; then
    echo "[WARN] 429 retry limit, falling back to youtube-transcript-api"
    # 改用 python youtube-transcript-api
    break
  fi
  WAIT=$((60 * RETRY))
  echo "[WARN] Rate limited, waiting ${WAIT}s before retry $RETRY/$MAX_RETRIES"
  sleep $WAIT
done
```

## 7. Gemini API 429 / 額度超標處理（Step 02 分析階段）

當 `video_analyzer.py` 在 `generate` 階段遇到 `429 RESOURCE_EXHAUSTED`（月額度用盡）：

1. **影片已下載完成**（`video_source.mp4` 在工作目錄，`analysis.json` 的 `metadata.local_video_path` 有本地路徑）——這個產出不會消失
2. **Gemini 檔案已完成上傳**（`files/xxx` state=ACTIVE）——第二次執行時腳本會重用上傳結果
3. **不需要重新下載影片**——直接用 `analysis.json` 的 `metadata.local_video_path` 作為下次輸入

### 重試策略

```bash
# 等 30-60 秒後，用本地檔案 + --keep-file 重試
# 先以 video_analyzer.py 實際 DEFAULT_MODEL 為準；2026-07-18 實測為 gemini-3-flash-preview。
# 長影片優先切成約 60 分鐘段落，各段分析後把後段 timestamp 加回 offset。
# 只有當實際腳本或 provider 明確要求相容性降級時，才指定其他模型；不要把舊 2.5-flash 命令當默認流程。
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/video_analyzer.py \
  "/path/to/video_source.mp4" \
  -o analysis.json --keep-file --model "gemini-3-flash-preview"
```

### 為何 `--keep-file` 重要

第二次執行時若附 `--keep-file`，`video_analyzer.py` 會：
- 直接上傳本地檔案（不重新下載 YouTube）
- 在 429 發生時，**Gemini 檔案 URI 仍存在**，可用本地路徑重試
- 節省 30-60 秒上傳時間 + 不重新下載影片

### 模型降級注意

- `gemini-2.0-flash` 已於 2026 年停用（404 NOT_FOUND），**不可再做為降級選項**
- `gemini-2.5-flash` 是目前唯一穩定可用的降級目標
- 若 `gemini-2.5-flash` 仍 429，代表月度 billing limit 真的用盡（而非模型問題）
  - 此時仍可繼續 **Step 04 字幕萃取**（不依賴 Gemini）
  - Step 02/03（視覺分析）需等額度恢復或手動提供分析結果
  - 若本輪需要先交付文章：可降級為「字幕主導解讀文」，但必須明確標註 quality_badge、在回覆中說明無視覺截圖，且嚴禁幻想畫面或硬塞不存在的配圖
  - `analysis.json` 可能完全不存在或是 0 bytes；此時不要依賴 `analysis.json.metadata.local_video_path`，改用工作目錄中的 `video_source.mp4` 或重新確認本地影片檔存在後再處理字幕/後續人工截圖
  - 若字幕可用，繼續 Step 04→05→06→07.5→08：主題地圖、純文字草稿、字幕忠實度檢查、Final Gate 與穩定預覽都照跑；Step 03 配圖與 vision QA 標記為 blocked/cancelled，不要硬做
  - 最終交付時通知使用者：本文是字幕主導版本，配圖待 Gemini 額度恢復或人工確認後補入

### Gemini 額度調整

若遇到 429 並確認是 billing limit：請使用者至 https://ai.studio/spend 調高額度上限。調整後等待 1-2 分鐘再重試。

### ffprobe / ffmpeg PATH 問題（subprocess 情境）

當 `video_analyzer.py` 由 OpenClaw 的 `sessions_spawn` 或 `delegate_task` subprocess 呼叫時，subprocess 的 `$PATH` 不繼承登入 shell 的 PATH，導致 `ffprobe` 或 `ffmpeg` 找不回 `No such file or directory`。

**徵兆**：`ffprobe failed to get duration: [Errno 2] No such file or directory: 'ffprobe'`（但直接執行指令時是好的）

**解法**：在 terminal 指令中明確指定完整路徑：
```bash
/opt/homebrew/bin/ffmpeg -y -i "$VIDEO" -ss "$ts" -vframes 1 "$WORK/frames/frame_${ts//:/_}.jpg"
```

或在使用 OpenClaw subprocess 時，在指令前注入 PATH：
```bash
PATH="/opt/homebrew/bin:$PATH" python3 /path/to/video_analyzer.py ...
```

常見工具路徑（macOS Homebrew）：
- ffmpeg: `/opt/homebrew/bin/ffmpeg`
- ffprobe: `/opt/homebrew/bin/ffprobe`
- yt-dlp: `/opt/homebrew/bin/yt-dlp`

---

## 8. Gemini 長影片 processing timeout / 大檔案視覺分析降級

當原始長影片（例如 4K、40 分鐘以上、接近 1GB）已成功上傳 Gemini File API，但 server-side processing 持續 `GET /files/... 200 OK` 最後超過 10 分鐘 timeout，不要把它等同於額度不足，也不要立刻放棄視覺分析。這通常是影片檔太大或編碼/解析度讓 Gemini 處理太慢。

### 已驗證 fallback：製作 visual-only proxy

保留完整時間軸，但降低視覺負載：

```bash
/opt/homebrew/bin/ffmpeg -y \
  -i /absolute/path/original.mp4 \
  -an -vf "fps=1,scale=-2:360" \
  -c:v libx264 -preset veryfast -crf 32 \
  video_visual_1fps_360p.mp4

/opt/homebrew/bin/ffprobe -v error \
  -show_entries format=duration,size \
  -of default=noprint_wrappers=1 \
  video_visual_1fps_360p.mp4
```

然後用 proxy 跑 Gemini：

```bash
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/video_analyzer.py \
  video_visual_1fps_360p.mp4 \
  -o analysis.json --keep-file --model gemini-2.5-flash
```

實務效果：47 分鐘 4K 影片可被壓成約 20MB、完整保留時間軸，Gemini processing 可從 10 分鐘 timeout 降到約 1 分鐘內完成。注意：proxy 只用於「找高價值時間點與畫面描述」，後續截圖仍要回到原始影片抽 frame，避免低解析圖入稿。

### `extract_assets.sh` / frame_aligner 手動抽圖 fallback

若 `extract_assets.sh` 在第一張 frame 直接退出，或 terminal 只停在類似 `--- Key Frames: N ---` / `[1/N] 00:43 — ...` 就 exit 1、沒有更多錯誤訊息，通常是 `frame_aligner.py` 內部失敗但 stderr 被腳本重導到 `/dev/null`。不要把素材流程卡死，也不要重跑整支影片分析。

處理方式：
1. 先確認 `analysis.json` 已成功且 `metadata.local_video_path` / `video_source.mp4` 存在。
2. 用 Gemini 回傳的 timestamp 從原始影片直接抽高解析圖：`ffmpeg -y -ss <秒數> -i video_source.mp4 -vframes 1 -q:v 2 -update 1 outputs/images/frame_NN_MM_SS.jpg -loglevel error`。
3. GIF 直接用同一段 `ffmpeg -ss <start> -t <duration> -i video_source.mp4 -filter_complex "[0:v] fps=12,scale=1080:-1:flags=lanczos,tpad=stop_mode=clone:stop_duration=1.5,split [a][b];[a] palettegen=max_colors=256 [p];[b][p] paletteuse=dither=floyd_steinberg" outputs/images/gif_NN_START-END.gif`。
4. 手寫相容 manifest，至少同時放在工作目錄根的 `manifest.json` 與 `outputs/images/manifest.json`，每個 asset 保留 `file/type/timestamp(or start_time/end_time)/description/importance/article_context`，讓 Step 07 子代理可正常配圖。
5. 之後仍必須做 contact sheet / vision QA，確認不是黑屏、空框、純人物或不可讀圖，再入稿。

若確認是環境依賴（例如 `opencv-python is not installed`），可另外修依賴；但當前文章流程應優先用手動 ffmpeg fallback 保住素材產出。

### 入稿注意：不要把圖片插進 YAML frontmatter

自動插圖時，搜尋 anchor 不能只用會出現在 `hamster_note` 的短句（例如「從不信任開始是理性的」）。先限定搜尋正文區域（frontmatter 第二個 `---` 之後），或用完整正文段落 anchor；否則圖片 Markdown 可能被插進 frontmatter，導致 preflight 解析不到 title/note/source。

---

## 9. 標準 caveat 語句

### Auto captions 清理後使用
`註：本文主要根據 YouTube 自動字幕整理，已做語句清理，但少數術語仍可能與原片略有出入。`

### 來源資訊密度偏低
`註：原影片有部分鋪陳與非核心內容，本文已聚焦保留主要觀點與實際有用的部分。`

### 無法完成完整文章
`這支影片目前缺少足夠可用字幕；若你要完整文章版，請改給我有字幕版本，或直接提供 transcript。`

### 429 阻斷（yt-dlp）
`影片下載被 YouTube 阻斷（429），稍後再試或手動提供影片檔案。`

### Gemini 額度超標阻斷
`影片視覺分析被 Gemini 額度超標阻斷，請至 https://ai.studio/spend 管理額度。字幕與文章內容不受影響，配圖待額度恢復後補入。`
