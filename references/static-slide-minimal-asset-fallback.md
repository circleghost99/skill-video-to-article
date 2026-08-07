# V2A 靜態投影片影片：Extractor 失敗時的最小可用素材路徑

## 適用情境

`video_analyzer.py` 成功，但只回傳少量 key frames（例如只有 00:05 標題頁）。接著 `extract_assets.sh` 在第一張 frame 就 exit 1，常見原因是 `frame_aligner.py` 依賴或環境問題。這種失敗不應阻斷整篇文章，尤其影片本身視覺資訊有限、文章主要靠逐字稿深度解讀。

## 收斂流程

1. **先確認 `analysis.json` 已成功且 key frame 數量很少**
   - 讀回 `content_summary`、`video_info`、`key_frames`、`metadata.local_video_path`。
   - 若 Gemini 只找到標題頁，後續不要幻想更多影片截圖。

2. **用 ffmpeg 直接抽已驗證時間戳**
   ```bash
   mkdir -p images/images
   ffmpeg -ss 5 -i video_source.mp4 -vframes 1 -q:v 2 -update 1 images/images/frame_01_00_05.jpg -y -loglevel error
   ```

3. **手寫相容 `manifest.json`**
   - 至少包含 `file`、`type`、`timestamp`、`description`、`importance`、`article_context`。
   - `file` 保持相對於 images dir 的檔名，供 Step 07 插圖子代理使用。

4. **仍必須做視覺 QA**
   - 用子代理或本地 QA 確認該 frame 非空白、非純人物、文字清晰，且符合 Gemini 描述。
   - 若不符合，在 ±1–2 秒候選幀中選最佳；都不符合就從 manifest 移除。

5. **文章透明處理**
   - 對公開讀者不要寫 pipeline caveat。
   - 對使用者回報時說明：影片證據圖只有標題頁，其餘配圖改用 baoyu / Codex 概念圖輔助理解。

## 2026-06-16 實例摘要

Kaggle / Google `Agent Tools & Interoperability` podcast 視覺上幾乎是靜態標題頁。Gemini 只回傳 1 張 key frame。`extract_assets.sh` 因 frame alignment 流程失敗未產出圖，但直接 ffmpeg 抽 00:05 標題頁成功，QA 後保留為唯一影片證據圖。文章另外用 Codex 概念圖補閱讀節奏。
