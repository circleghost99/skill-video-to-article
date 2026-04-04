---
name: video-to-article
description: 把單支有字幕的 YouTube 影片轉成結構化、可閱讀、可發佈的文章草稿。當需求是把一支 YouTube 影片的字幕內容重組成解讀型文章、深度筆記或 markdown 長文，而不是短摘要、逐字稿清理、純翻譯、單純截圖或多影片整合時使用。v1 優先處理字幕可取得的 YouTube 單片流程。
---

# Video to Article

這個 skill 專門處理：**把單支 YouTube 影片轉成文章。**

v1 先把主流程做好：
- **YouTube-first**
- **single-video only**
- **captions-available first**
- **article synthesis first**

先不要把它當成多影片研究引擎，也不要把它當成逐字稿清理器。

## 參考檔案 (References)

在執行特定子任務時讀取對應參考：
- `references/examples.md` — 觸發範例、非觸發情境、v1 預期結果
- `references/workflow-technical.md` — YouTube 字幕取得、暫存目錄、技術步驟
- `references/fallbacks.md` — 字幕品質判定、降級規則、v1 停損點
- `references/output-format.md` — 解讀型文章標準、段落骨架、標題與洞察寫法
- `references/visual-extraction.md` — 只有在影片畫面真的有解釋價值時才讀
- `references/deployment-cleanup.md` — 交付、確認、同步、清理
- `references/notion-sync.md` — 只有要同步 Notion 時才讀
- `references/hamster-profile.md` — 僅在 hamster flow 讀取

## 邊界定義 (Boundary)

這個 skill 是 **單支有字幕 YouTube → 解讀型文章** 的 skill。

### 會做
- 抽出影片核心命題與價值主張
- 把字幕內容重組成文章邏輯，而不是照時間軸平鋪
- 交付可閱讀的 markdown 長文或深度筆記

### 不做
- 短摘要 / TL;DR
- 純逐字稿整理
- 逐句翻譯
- 單純影片下載或截圖
- 多影片整合（留待後續版本）
- 無字幕影片的完整 fallback 主流程（v1 不主打）

## 核心流程 (Core Strategy)

### 1. 先確認來源與字幕
- 先確認是 YouTube 影片，並檢查字幕是否可取得。
- 優先使用人工字幕；若只有 YouTube auto captions，確認品質可接受再繼續。
- 若沒有可用字幕，依 `references/fallbacks.md` 停下或降級，不要硬寫完整文章。

### 2. 先整理字幕，再整理文章
- 先把字幕清成可分析文本，再做主題地圖。
- 不要一邊看字幕一邊直接寫稿，這樣很容易退化成摘要或改寫逐字稿。
- 先抽：核心問題、核心主張、關鍵機制、例子、限制、真正的洞察。

### 3. 文章要重組，不要照時間軸抄
- 預設要把影片內容重組成「問題 → 方法 / 觀點 → 為什麼重要 → 實際意義」的文章邏輯。
- 只有當影片本身就是 step-by-step demo 時，才保留較強的流程順序。

### 4. 視覺素材是加分，不是主體
- v1 先以字幕驅動的文章為主。
- 只有當畫面本身承載額外資訊時，才讀 `references/visual-extraction.md` 做截圖 / GIF。
- 對概念解說型影片，不要為了湊圖而湊圖。

### 5. 先交 review-ready draft
- 強制做一次 review pass：檢查有沒有遺漏關鍵論點、把時間軸口語殘留在文章裡、或把作者觀點寫扁。
- 先交 review-ready draft，再等使用者確認。

### 6. 確認後才同步與清理
- 依 `references/deployment-cleanup.md` 執行同步與清理。
- **未確認前，不要清掉中繼檔。**

## 操作原則 (Principles)
- **先把 happy path 做穩。** v1 先吃有字幕單片，不急著把所有 fallback 與多來源整合做滿。
- **文章優先，不是 transcript 優先。** 字幕只是原料，交付物必須是可讀文章。
- **解讀比摘錄重要。** 不只寫「講了什麼」，要寫「為什麼重要」。
- **少而準。** 若影片資訊密度有限，就寫成紮實的短篇解讀，不要硬灌水。
- **安全第一。** 不在 skill 內放 secrets 或特定環境憑證。
