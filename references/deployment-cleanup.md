# Deployment & Cleanup Reference

This reference covers the final stages of the video-to-article workflow: delivery, confirmation, and post-task maintenance.

## Final Review & Delivery

The primary goal is to present a **Review-ready Draft** to the user. Do not finalize or delete intermediate assets until the user confirms.

### Delivery Presentation
In the thread or conversation, present:
1.  **Draft Article**: The main output (markdown).
2.  **Asset Summary**: List of screenshots and GIFs generated and their locations.
3.  **Handoff message**: "Here is the draft. Please confirm if any changes are needed. Once approved, I will sync to your knowledge base and clean up temporary files."

## 1. Destination-Specific Syncing

If the user gives the "OK" (e.g., "OK", "Approved", "Looks good"), proceed to sync:

### Obsidian (Default Local)

**Vault 路徑**：`~/Library/Mobile Documents/iCloud~md~obsidian/Documents/知識庫/`

**Output 資料夾結構**：
```
知識庫/
└── 影片解析/
    └── {YouTube_ID}_{影片標題縮寫}/
        ├── {文章標題}.md
        └── images/
```

**執行流程**：
1. 複製最終 markdown 到 `影片解析/{ID}_{標題}/` 目錄
2. 複製所有確認的截圖/GIF 到 `images/` 子目錄
3. 將 markdown 中的圖片路徑改為相對路徑 `./images/檔名`
4. **不要**刪除中繼檔，直到使用者在 Obsidian 確認 OK
5. 確認後再清理 `frames/explore/` 等暫存

### Notion (External)
- If the workflow is Notion-bound, refer to `references/notion-sync.md`.
- Ensure all properties (lead visual, reflection fields) are correctly mapped.

## 2. Post-Confirmation Cleanup

**Crucial: Do not run cleanup before the user says "OK".**

Once confirmed and synced:
1.  **Delete Middle-stage Assets**:
    - Remove the source video (`video.mp4`).
    - Remove the exploration frames folder (`frames/explore/`).
    - Remove any intermediate testing frames.
2.  **Run Cleanup Script**: Execute `scripts/cleanup_temp_dirs.sh` to clear the current session's temp directory and any stale ones.
3.  **Completion Notification**: Inform the user: "Article synced to [destination]. Temporary assets (video, exploration frames) have been cleared."

## 3. Deployment Constraints
- No secrets or environment-specific credentials in skill files.
- If a destination (e.g., a specific Notion database ID) is missing, ask the user.
- If syncing fails, preserve the local draft and report the error; do not discard the result.
