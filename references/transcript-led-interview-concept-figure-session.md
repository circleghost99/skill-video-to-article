# Transcript-led interview + concept figures

適用：使用者明確要求深度解讀一支訪談，並指定不用 Gemini 視覺分析，但仍要求文章配圖。

## Canonical workflow

1. 建立 profile-owned absolute workspace：`outputs/interviews/<VIDEO_ID>/`。
2. 先取得字幕與 metadata。自動字幕若出現 rolling-caption 重複、句段覆蓋或明顯重複，不能直接進入寫作；改抓 canonical／較可靠來源，並記錄來源與覆蓋範圍。
3. 將字幕轉成帶時間碼與行號的工作稿，抽取主題地圖與 claim ledger。每個核心主張記錄 transcript 行號、數字、案例、證據層級與不可過度延伸的限制。
4. 外部研究要真正進正文，不只放 Sources。優先查一手或官方資料，對每個來源記錄 URL、身份、可驗證重點、正文放置段落與限制。不得用 blocked 或猜測的 URL。
5. 以 transcript-led 模式寫文章：前言先處理讀者痛點，正文從 H2 開始，明確分開訪談主張與編輯推導；Bob／講者個案的時間與倍數必須寫成個案估算，不可升格為普遍 benchmark。
6. 文章完成後才規劃概念圖。概念圖是解釋框架，不是影片證據，也不能暗示畫面曾在影片中出現。優先選 comparison、flowchart、framework、timeline／ladder，依 H2 內容插入，不能全部 append 到文末。

## Image QA gate

- 文章概念圖使用 Codex native-only 路徑；保留每張 PNG 的 provenance sidecar，確認 `backend=codex`、`native_only=true`、`postprocessing=[]`、`native_violation_detected=false`。
- 每張圖 prompt 明列 Type、Style、Palette、Layout；所有圖內繁中標籤每個不超過 8 字，禁止額外英文、偽字、數字與微文字。
- 四張以上圖片使用 explicit ffmpeg xstack／hstack／vstack 建 contact sheet，確認輸入數量與文章實際嵌入清單一致。
- Contact sheet 只能作整組檢查，仍要逐張 full-resolution vision QA：文字逐字核對、品牌 lockup、箭頭／流程、角色是否融入構圖、是否有空白或裁切。子代理回報不能取代主 Agent 驗收。
- 通過 QA 後，圖片以絕對路徑插在對應完整段落之後；每張附描述性 alt text 與一句 caption。檢查沒有連續圖片，且圖片之間有實質文字。

## Text fidelity and release gate

- concept figures 插入或任何手動修改後，重新做 fidelity check，至少核對數字、反直覺金句、具名案例／流程細節；必要時列出 critical、nice_to_have、out_of_scope。
- Final Gate 必須在最後一次修改後執行。至少檢查 frontmatter、無 H1、無 HTML tag、無 em dash、無 corruption、無中英黏連、圖片路徑存在、無連續圖片。
- 預覽稿與 fidelity report 應使用 profile-owned 穩定絕對路徑。未經使用者確認，不直接發布 Notion。

## Session-specific lesson

這類訪談常可在不做任何 Gemini 視覺分析的情況下產出高品質文章，但仍要明確標記「沒有影片畫面證據」，避免把概念圖混稱為 evidence frame。對本文型訪談，外部來源的限制聲明與 transcript 行號比空泛的影片畫面描述更有價值。
