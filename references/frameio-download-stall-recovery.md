# Frame.io 下載卡住排查與有界 fallback

適用於多影片 Frame.io share series。這份 reference 記錄可重用的下載排查，不代表某個單一 asset 永久失效。

## 症狀與判定

- 直接開深層 asset URL 後，頁面出現 Frame.io Login 控制項、只有麵包屑或空集合，沒有 `asset-panel-grid-asset-card`。這是分享路徑／session 狀態問題，不是影片不存在。
- `.crdownload` 連續兩次檢查的 size 與 mtime 都不變，且 Chrome History 沒有該檔案的正常 download record，可判定為停滯／孤兒暫存檔。不要把它當完成檔，也不要無限輪詢。
- Frame.io Download menu 可能先跳出下載方式對話框；監控程序看到 `DONE` 不代表下載成功，必須確認完整 `.mp4` 已出現，再用 `ffprobe` 驗證 duration 與 size。

## 正確重試順序

1. 回到 canonical share root，沿公開 folder tree 進入 parent folder，再從可見 asset card 開啟影片。不要重用 stale numeric refs；每次頁面更新後重新取得 DOM ref。
2. 使用 asset card 內的 semantic `Download Asset` 控制項。若出現選項，明確選 `Download in Browser` 或指定 proxy，不要猜 signed URL。
3. 原始檔只重試一次。若失敗，或 `.crdownload` 的 size/mtime 在兩次間隔檢查不變，停止監控並保留暫存檔供後續清理。
4. 選明確標示的 proxy，優先 MP4 H264 1280×720；它可用於字幕、ffprobe、抽幀與視覺 QA，但文章／fidelity 必須透明標示使用 proxy。若 proxy 也失敗，將 exact error 與 `download_stalled` 寫入 `series_manifest.json`，直接處理下一支。
5. 完成檔出現後立即：`ffprobe -v error -show_entries format=duration,size -of json FILE`。只有 duration、size 和 MIME 合理才標為 downloaded。

## 證據與清理

- `series_manifest.json` 應記錄 `download_variant`（original/proxy）、`original_download_status`、本機絕對路徑、transcript/evidence/article/fidelity、Drive file ID、Drive permission readback、Notion page/readback 與 `video_deleted`。
- Drive upload JSON 只是建立訊號；用 `gog drive permissions FILE_ID --account ACCOUNT --json` 確認 `permissionCount: 1` 且唯一 role 是 owner。
- Notion 使用 `preflight → publish/update → full readback`。平台 OpenCC 誤轉要修本地 source 後 update 同一 page，不要另建頁。
- YouTube 若使用者確認暫不等待，不是本輪清理 blocker；以 Drive 唯一 owner + Notion full readback 作為刪除本機影片 Gate。失敗的 `.crdownload` 可在最後清理階段一併移除，但不可拿它作影片備份或文章輸入。

## 回報用語

區分「原始下載失敗」與「proxy 成功」。不要回報成『影片下載完成』而隱藏 proxy；應寫成『原始 3.73 GB 串流停滯，經 folder-tree 路徑改取 1280×720 proxy，proxy 已通過 ffprobe 與視覺 QA』。