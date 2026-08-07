# Gemini 3 分段視覺分析重試與合併

## 觸發條件

原始影片因 Gemini project spending cap、上傳大小、長影片 processing timeout，或**整片分析成功但回傳 JSON 格式錯誤**而需要重試。典型 parse failure 是模型把 `video_info.duration_seconds` 寫成未加引號的 `104:28`，導致 `Expecting ',' delimiter`；這代表視覺推理請求已完成，但結構化輸出不可用，不應降級成「Gemini 無法分析影片」。

遇到 parse failure 時，若腳本只保存 `raw_response_preview` 而沒有完整 response，不能憑截斷 preview 手補 key frames。改用既有本地影片切段重跑，保留可稽核的完整 JSON。

## 標準流程

1. 先讀 `video_analyzer.py` 的實際 `DEFAULT_MODEL`，不要直接照舊 fallback 文件指定模型。2026-07-18 實測腳本預設為 `gemini-3-flash-preview`；舊文件中的 `gemini-2.5-flash` 只可作明確相容性 fallback，不應默認使用。
2. 對超過約 60 分鐘的影片，使用原始本地影片切成 60 分鐘左右的無音訊段落。保留每段起始秒數，例如 part 2 offset=3600。
3. 每段分別執行 `video_analyzer.py`，輸出獨立 `analysis_partNN.json`。prompt 要求：只收完成畫面、排除 talking head／轉場／logo、提供 `timestamp`、`description`、`article_context`。若前次是 JSON parse failure，prompt 還要明示：`video_info.duration_seconds` 必須是**純整數秒數**，不可寫 `MM:SS`；`timestamp` 才使用 `MM:SS` 字串。這可避免 `duration_seconds: 104:28` 破壞整份 JSON。
4. 讀回每份分析的 metadata、key frame 數、GIF 數、成本與摘要；不能只看 terminal 長 log。若任一 part 仍 parse 失敗，只重跑該 part，不重跑已成功的分段。
5. 合併時把後續分段的 `timestamp`、`start_time`、`end_time` 加上 segment offset，再按完整影片時間排序；對相隔很近且描述重複的幀做去重。合併產物應保留 `source_part` 與數值型 `timestamp_seconds`，並把 `metadata.local_video_path` 指回原始高解析影片的絕對路徑。
6. 用原始高解析影片依合併後 timestamp 抽圖，不要用低解析切段檔作文章圖片。GIF 也從原始影片擷取。
7. 建立 Gemini contact sheet，主 Agent 親自做視覺 QA。刪除模糊／載入／黑色播放器／螢幕遞迴干擾過重／重複幀；不要把子代理或 Gemini 摘要視為主 Agent 已看過畫面的替代品。
8. 將通過 QA 的 Gemini evidence frames 替換或補入文章，更新圖片 alt text，使 alt 與實際畫面主題一致。若某個候選仍是黑色播放器或畫面未播放，換成更晚 3–5 秒的候選，仍不清楚就刪除。
9. 文章最後一次圖片或文字修改後，重跑完整 Final Gate。Final Gate 若因 zhtw/OpenCC 將「導入 AI」變成「匯入 AI」、將「權限」變成「許可權」、將「只看」變成「隻看」等語意誤轉，先人工修回，再只跑輕量格式／路徑／連續圖片檢查，避免完整 Gate 再次覆寫。

## 已驗證結果

2026-07-18，6704 秒影片切成 3600 秒 + 3103.6 秒，Gemini 3 Flash 兩段皆成功；合併得到 30 key frames、4 GIF candidates。contact sheet QA 後，frame 03（模糊）、frame 24（黑色面試播放器）、frame 26（遞迴干擾）列為換幀或刪除候選。這些數字只是流程實例，不是固定產量要求。

## 透明回報

若先前曾錯誤啟動舊模型，需明確說明舊 process 已停止、成功結果來自哪個實際模型；不要把被 SIGTERM 的舊任務誤報為新任務失敗。