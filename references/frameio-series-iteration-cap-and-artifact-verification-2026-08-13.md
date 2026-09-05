# Frame.io 系列：回合上限與產物驗證紀錄（2026-08-13）

## 可重用問題

多支 Frame.io 影片連續處理時，工具回合可能在某支影片剛選取資產後耗盡。此時聊天紀錄不是可靠 checkpoint：子代理可能回報已寫檔，但檔案尚未落地；背景 Notion/Drive 程序可能已啟動，卻沒有把結果回傳到主回合。

## 正確判定

- `delegate_task` 的 `completed` 只代表子代理回報，不代表目標檔案已存在。用絕對路徑檢查檔案存在、非空、frontmatter 完整，再進 preflight。
- background process 的 started/exited 訊息不是遠端成功證明。必須讀 JSON 回傳，或用目的地搜尋/權限讀回取得實際 file ID、page ID、URL。
- `series_manifest.json` 是跨回合 source of truth。每支影片至少記錄：index、asset/source URL、local path、duration/size、transcript path、evidence dir、article path、Drive file ID、Notion page ID、readback status、youtube status、video_deleted。
- 接近 iteration cap 時，停止非阻擋診斷與額外探索。先完成當前項目最小可驗證收尾，寫回 manifest，再以「已完成 / 進行中 / blocked / 尚未開始」回報。

## 本輪驗證出的兩個品質陷阱

### 1. 子代理寫作產物缺席
第二支子代理曾回報文章完成，但指定 article/report 路徑實際不存在。後續不能直接 publish；應把狀態保留為 article pending，直到檔案實際落地。

### 2. Notion 二次 OpenCC 轉換
本地 Final Gate 或 preflight 通過，publish/update 仍可能在遠端把 `權限`、`平台`、`不是只` 等詞轉成不自然形式。正確修法是：

1. 用 full blocks readback 掃遠端正文，而非只看 publish JSON。
2. 找出受影響句子，優先自然改寫成不易觸發轉換的詞，如 `存取控制`、`系統`、`不只` 的重寫句。
3. 對同一 page `update`，不要建立第二頁。
4. 再次 readback，要求 bad-term scan = 0，並確認 block/image count 不變或符合預期。

## 主代理寫入安全

子代理可能在主代理上次讀檔後修改文章。每次 patch 前重新讀取 frontmatter 與受影響段落，避免把 `source_url`、tags 或其他 YAML key 覆蓋掉。若 patch 造成 YAML key 遺失，立即修回並重新讀檔驗證。

## Contact sheet 限制

現有 contact-sheet helper 一次最多處理四張圖；輸入超過四張時可能印出 warning 但仍產出檔案。大量抽樣必須拆成多張 sheet 或使用明確 grid，並核對文章真正使用的每張圖都在 QA 範圍內。