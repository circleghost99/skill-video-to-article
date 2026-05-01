# YouTube v1 Fallbacks & Downgrade Rules

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

1. **立即切換到 `youtube-transcript-api`**（首選繞過方案，不需 impersonate）
2. 只有當 `youtube-transcript-api` 也不可用時，才進入退避重試流程
3. **退避重試**：等待 60-120 秒，以指數退避重試，最多 3 次
4. 仍失敗 → 停下，回報使用者

### `youtube-transcript-api` 使用方式

```bash
python3 -m pip install youtube-transcript-api --break-system-packages
```

```python
from youtube_transcript_api import YouTubeTranscriptApi
api = YouTubeTranscriptApi()
transcript_list = api.list(video_id='VIDEO_ID')
for t in transcript_list:
    if t.language_code == 'zh':
        segs = t.fetch()
        data = [{'start': s.start, 'duration': s.duration, 'text': s.text} for s in segs]
```

**範例退避 script（yt-dlp fallback）：**
```bash
RETRY=0
MAX_RETRIES=3
until yt-dlp --write-subs --write-auto-subs --sub-langs ... "$URL"; do
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

## 6. 標準 caveat 語句

### Auto captions 清理後使用
`註：本文主要根據 YouTube 自動字幕整理，已做語句清理，但少數術語仍可能與原片略有出入。`

### 來源資訊密度偏低
`註：原影片有部分鋪陳與非核心內容，本文已聚焦保留主要觀點與實際有用的部分。`

### 無法完成完整文章
`這支影片目前缺少足夠可用字幕；若你要完整文章版，請改給我有字幕版本，或直接提供 transcript。`

### 429 阻斷
`影片下載被 YouTube 阻斷（429），稍後再試或手動提供影片檔案。`
