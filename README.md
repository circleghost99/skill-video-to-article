# ⚠️ DEPRECATED — 這個 skill 已於 2026-09-05 拆分退役

`video-to-article` 原本同時做兩件事：影片證據抽取（字幕、視覺分析、關鍵幀）與文章寫作（初稿、審校、發布前 gate）。因為寫作能力已經獨立成熟，2026-09-05 拆成兩個 skill：

| 新 skill | 負責 | repo |
|---|---|---|
| **video-evidence** | 影片證據抽取：字幕、Gemini 視覺分析、關鍵幀 + 回讀驗證、主題地圖 | `circleghost99/skill-video-evidence` |
| **hamster-writing-craft** | 寫作方法論、審校、完整性檢查、發布前 final gate（`final_gate.py` 已移入） | `circleghost99/skill-hamster-writing-craft` |

## 使用者該做什麼

不要再從這個 repo 安裝。改裝上面兩個之一：

- 影片畫面本身承載資訊（螢幕操作、步驟、簡報、Demo、UI）→ 用 `video-evidence` 抽證據，再交給 `hamster-writing-craft` 寫。
- 訪談、podcast、對談 → 只需要字幕，用 `video-evidence` 的字幕模式，或直接用 `hamster-writing-craft`。

## 這個 repo 還留著做什麼

保留 commit 歷史供追溯。內容已封存（read-only），不再更新。46 份 references 的拆分對照見 video-evidence repo 的 changelog。
