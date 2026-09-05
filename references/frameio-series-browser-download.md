# Frame.io 多影片系列：瀏覽器盤點與下載實務

## 已驗證流程

1. 先用 `opencli browser <session> open https://f.io/...`，取得實際 `next.frame.io/share/...` URL。
2. 不要只讀根頁的 asset cards。根頁可能顯示資料夾，直接進某個 asset URL 時也可能出現 `There are no assets available in this Folder`。先讀父資料夾 state，從資料夾連結進入真正子資料夾。
3. 在子資料夾 state 找到：
   - `data-testid=asset-panel-grid-asset-card`
   - `label=Select asset <filename>`
4. 點 asset card 開啟影片頁後，先點 Download 按鈕。選單通常分成：
   - `Original` / `Download original file`
   - `Proxy`，例如 `Proxy h264_720`
5. 點 `Download original file` 後，下載可能先以 `尚未確認的 <id>.crdownload` 出現。必須輪詢檔案，確認 `.crdownload` 消失並改成正式副檔名，再做 `stat` 與 `ffprobe`。

## 重要驗證欄位

每支影片在系列 manifest 至少記錄：

- `asset_id`
- `source_url`
- `title` / `filename`
- `duration_display`
- `local_download_path`
- `local_download_verified`
- `drive_file_id` / `drive_url`
- `drive_privacy_verified`
- `transcript_path`
- `evidence_dir`
- `article_path`
- `notion_page_id` / `notion_url`
- `notion_readback_verified`
- `youtube_status` 與實際錯誤（若 pending/blocked）
- `video_deleted`
- `status`

不要在未取得實際 asset card 或未等下載完成時填入這些欄位。

## YouTube 阻塞處理

YouTube Studio 的 file input 可能可被 state/find 看見，但 browser bridge 對 file upload 仍可能回傳 CDP `-32000 Not allowed`。這只代表當次上傳操作被瀏覽器權限或 bridge 限制阻擋，不代表 YouTube 永遠不可用。正確處理是：

- 把實際錯誤寫入 manifest，例如 `youtube_status=blocked_opencli_file_upload_not_allowed`。
- 不虛構影片 URL，也不宣稱已設為 Private。
- 繼續完成字幕、視覺 QA、文章、Notion 與其他雲端備份。
- 最後集中重試 YouTube，成功後必須讀回影片 ID 與 `privacyStatus=private`。

## 視覺 QA 邊界

影片抽幀必須先建立 contact sheet，再用 Vision 判斷是否有實體投影片、圖表、UI 或只有講者。字幕只能支持語音內容，不能替代畫面證據。若 Vision 確認只有講者畫面，不要在文章中捏造投影片；若確認有投影片，文章需清楚區分：

- 字幕說了什麼
- 親眼驗證畫面看到什麼
- 根據場次順序推導出的分析

## 清理規則

YouTube 未完成、Notion 未遠端讀回、或字幕／文章仍缺失時，不得刪除本機影片。只有所有必要產物已存在、雲端備份與 Notion 狀態已驗證，且 YouTube 的使用者要求已完成或明確被標記為延後，才可按系列 plan 進行影片清理。