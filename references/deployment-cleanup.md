# deployment-cleanup.md

## 交付流程

每次 article draft 完成後，確認後執行交付。

### 交付檢查清單

- [ ] Review pass 完成（檢查口語殘留、過度壓縮、邏輯斷裂）
- [ ] Frontmatter 齊備（title / source / duration / tags / quality_badge）
- [ ] 圖片已存 `outputs/images/`，使用相對路徑 `./images/xx.jpg`
- [ ] 確認要同步到 Obsidian 或 Discord（或兩者）

---

## Discord 交付

Discord **不支援** `file://` URL 或本地相對路徑 markdown 圖片。

**正確流程：**
1. 文章內文 → `message(action=send, message="...")` 純文字發送
2. 每張圖片 → `message(action=send, media="<絕對路徑>")` 用 `media` 參數上傳為附件
3. **禁止**在 Discord 訊息中使用 `![...](file:///...)` 或 `![...](./images/...)`

**圖片路徑：** 圖片存 `outputs/images/`，上傳時用 `message media=` 參數。

---

## Obsidian 交付

1. **Git commit** 到 `openclaw-skill-video-to-article`
2. **複製文章到 Obsidian**（iCloud 路徑）
3. **複製圖片到 Obsidian** 對應目錄

### Obsidian 路徑

影片解析文章 → `知識庫/影片解析/<VIDEO_ID>_<SLUG>/`

範例：
- `知識庫/影片解析/jpBOHpl0bvw_需求錯判/`
- `知識庫/影片解析/N519Nj7LRXA_OpenClaw技能養/`

iCloud Obsidian 路徑：
`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/知識庫/影片解析/`

---

## 清理

交付完成後，確認以下才清理 temp：
1. 文章已送達（Discord 回條或 Obsidian 同步確認）
2. 使用者已確認滿意
3. Temp 檔案（`TEMP_DIR/frames/` 等）可以清除

**未確認前不要清中繼檔。**

---

## 當前任務：jpBOHpl0bvw

狀態：待執行完整流程

目標影片：https://www.youtube.com/watch?v=jpBOHpl0bvw
