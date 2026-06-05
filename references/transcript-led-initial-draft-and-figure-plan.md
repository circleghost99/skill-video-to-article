# Transcript-led 初稿 + 配圖方案交付模式

適用情境：使用者要的是「某支影片的繁中深度解讀初稿與配圖方案」，且工作區已經有可用字幕 / metadata（例如系列影片已批次下載 transcript），但沒有要求完整 Notion 發布或完整 Gemini 視覺分析。

## 核心原則

這不是完整 v2a 發布 pipeline，而是「初稿交付」模式：先把可用 transcript 轉成 article-grade 初稿，再另外交付配圖 brief 與 fidelity report，讓後續主代理或人類編輯能接續生成圖片 / 上傳 Notion。

## 建議輸出三件組

1. `articles/<slug>-analysis.md`
   - 必須包含 YAML frontmatter。
   - 文章正文從 H2 開始，不寫 H1。
   - 寫成繁中深度解讀文，不是逐字稿摘要。
   - 若無實際截圖，不要硬插本地圖片 placeholder 到正文。

2. `figures/<slug>-figure-brief.md`
   - 每張圖包含：建議位置、圖像目的、畫面構圖、圖中文字草案、生成提示詞。
   - 以概念圖 / 架構圖 / 對照圖為主，避免把未知影片畫面當成已驗證事實。
   - 若影片主軸是工具架構或 agent stack，優先把產品清單轉成「風險分層 / 工作流 / 介面分工」圖。

3. `reports/<slug>-fidelity.md`
   - 把 transcript 裡支撐文章的關鍵證據列成行號索引。
   - 區分「已引用」、「nice_to_have」、「out_of_scope」。
   - 特別標註任何主代理按常識修正的術語（例如字幕誤聽 JSON RPC）供後續對照影片畫面。

## 寫作注意

- 可直接用 transcript 行號作為 source-of-truth，避免把整份字幕灌入主 context 反覆改寫。
- 初稿應保留具體數字與機制：例如「三個痛點」「四個元件」「兩行程式」「三個檔案」這類可支撐論點的顆粒度。
- 沒有做視覺分析時，不要宣稱「影片畫面顯示」；改寫成「講者說明 / 示範段落 / 影片主張」。
- 可用簡短 deterministic check 驗證輸出檔：HTML tag=0、em dash=0、正文中文字數 / token-ish 統計。

## Final response contract

回覆使用者時簡短列出：
- 文章路徑
- 配圖 brief 路徑
- fidelity report 路徑
- 基本 QC 結果（例如 HTML tag / em dash / 字數）
- 需要後續主代理注意的 1-2 個審稿點

不要把整篇文章貼回 Discord，除非使用者明確要求預覽全文。
