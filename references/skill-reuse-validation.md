# Skill Reuse Validation Protocol

用於測試 `video-to-article` skill 是否可被 fresh agent 穩定複用。這不是正式發佈流程；目標是驗證 workflow、產物品質與 guardrail 是否真的被遵守。

## 何時使用

使用者說：

- 「驗證 skill 複用性」
- 「再派一個 agent 跑看看」
- 「dry-run，不要發布」
- 「測一下 Final Gate」

## 嚴格邊界

Dry-run 中禁止：

- 上傳 Notion
- 發正式 Discord 特報
- 同步 Obsidian 發佈區
- 執行 cleanup，除非使用者明確要求

Dry-run 中允許：

- 生成或重用本地 artifact
- 產出 contact sheet 給使用者參考
- 跑 Step 08 Final Gate
- 修本地 copy / draft，直到 Final Gate 通過

## 建議拆成兩層驗證

### A. Artifact-level validation（優先）

當已有真實 v2a 工作目錄時，優先拿 artifact 驗證，不要一開始就重跑完整影片分析。這能快速驗證 skill guardrail：

1. 複製 `article_draft.md` 到 `/tmp/...`，避免污染原稿。
2. 統計 frame / GIF 數量。
3. 每個 GIF 抽首幀與尾幀，用 vision 驗證是否完整、有意義。
4. 在 copy 上跑 `python3 ${HERMES_SKILL_DIR}/scripts/final_gate.py <copy>`。
5. 若 Gate 失敗，只修 copy；修完重跑 Gate。

### B. Full pipeline dry-run（必要時）

只有當 artifact-level 通過後，才考慮完整 Step 01–08 dry-run。完整跑影片分析成本高、時間長，也容易受 CLI provider rate limit 或互動模式卡住影響。

## Hermes CLI 啟動建議

避免用沒有 `--yolo` 的背景長任務，容易卡在權限/互動確認而沒有 tool steps。

建議：

```bash
hermes -p hamster --yolo chat \
  --source v2a-skill-reuse-test \
  -t terminal,file,skills,vision \
  -q 'Artifact-level dry-run validation for video-to-article skill...'
```

若需要 background，必須：

1. 設 `notify_on_complete=true`。
2. 1–2 分鐘內用 `chain_summary(source=...)` 或 `process.poll` 確認有 tool steps / output。
3. 若 5 分鐘仍 0 steps / 0 output，視為 CLI 子程序卡住，停止該 run，改用 artifact-level validation。

## Final response contract

Dry-run final response 必須包含：

- PASS / FAIL
- session id（若有）
- 原始 workdir 或 artifact path
- 實際檢查的 article path
- contact sheet path（若有）
- frame / GIF 數量
- GIF 首幀 + 尾幀驗證摘要
- Final Gate 完整輸出
- 是否有修改 skill 或 reference 文件

## 判定規則

- 沒有 tool error 不代表通過。
- 文字上宣稱「已檢查」不算，必須有可定位的 Gate output。
- Notion 成功不代表 source file 乾淨；必須檢查本地 `article_draft.md`。
- Gate 必須在最後一次文章修改之後執行。
- 若 dry-run prompt 要求不發布，但 agent 上傳 Notion / 同步 Obsidian，直接判定 FAIL。
