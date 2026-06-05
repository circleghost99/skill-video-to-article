# Transcript-led 初稿 + 配圖方案模式

## 觸發場景

使用者要求「針對某支影片撰寫繁中深度解讀初稿與配圖方案」、「先給初稿和配圖 brief」、「不要上傳 / 不要正式發布」，且目前已有可用 transcript 或使用者只要求文字初稿時，可採用此輕量模式。

這不是完整 v2a 發布流程；目標是快速產出可供主代理 / 編輯接續使用的三個穩定 artifacts：

1. `articles/<slug>-analysis.md`：有 YAML frontmatter 的繁中深度解讀初稿。
2. `figures/<slug>-figure-brief.md`：概念型或截圖型配圖 brief，不假裝圖片已生成。
3. `reports/<slug>-fidelity.md`：逐字稿忠實度檢查與 nice-to-have 清單。

## 執行原則

- 明確標示此稿是 `transcript-led`，若未跑 Gemini 視覺分析 / ffmpeg 擷取，不能聲稱已插入影片截圖。
- 配圖方案可以是「概念型資訊圖 brief」或「建議擷取的影片畫面」，但要與實際圖片檔分清楚。
- 若沒有可靠影片 URL，可沿用既有 transcript 來源，但 frontmatter 的 `source_url` 不可硬編錯誤連結；未知就填空字串或 `TBD` 並在回覆中標註需主代理補。
- 初稿仍需遵守 output-format：frontmatter、本文從 H2 開始、無正文 `---`、無 HTML tag、無 em dash、繁中語氣。
- Fidelity report 必須列出 transcript 行號，分成「已覆蓋」、「待判斷 nice_to_have」、「已忽略」。
- Final 回覆不要貼整篇長文，交付路徑、字數、檢查結果、未處理 caveat 即可。

## 建議目錄

若已有系列 workspace，沿用：

```text
<workspace>/articles/<slug>-analysis.md
<workspace>/figures/<slug>-figure-brief.md
<workspace>/reports/<slug>-fidelity.md
```

若沒有 workspace，使用穩定輸出目錄：

```text
/Users/circleghost/.hermes/profiles/hamster/outputs/v2a/<slug>/
```

## 系列工作區與「第 N 篇」請求

當使用者只說「第 5 篇」「針對某系列第 N 支影片」而沒有貼 URL，但當前或既有輸出目錄中已有 playlist / transcripts / articles 結構時，優先沿用既有系列 workspace，不要另建散落目錄或要求使用者重貼 URL。典型做法：

1. 在穩定輸出目錄或已知系列目錄中尋找 `playlist_manifest.json`、`transcripts_status.json`、`transcripts/`、`articles/`、`figures/`、`reports/`。
2. 用 transcript 檔名前綴或 manifest 對應第 N 篇，例如 `05-...txt`。
3. 產出路徑沿用同一命名規則：
   - `articles/05-...-analysis.md`
   - `figures/05-...-figure-brief.md`
   - `reports/05-...-fidelity.md`
4. 若前幾篇已有文章，讀一篇鄰近成品作為系列格式範本，保持 frontmatter、標題密度、段落長度與回覆格式一致。
5. 如果 transcript 是自動字幕，常見會把產品名聽錯（如 Claude Code → Cloud Code / Claw / Cloud、Claude.md → cloud.mmd / claw.md）。文章與配圖 brief 應統一成正確正式名稱；fidelity report 可保留原 transcript 行號與原文來源，不必把來源錯字硬改掉。

## 快速 QC

補充案例：`references/transcript-led-code-with-claude-series-example.md` 記錄了 Code w/ Claude 系列第 N 篇的穩定目錄、三檔交付契約、QC 與 Claude 自動字幕術語修正模式。遇到同系列 numbered request 時可先讀該案例，沿用既有 workspace 與命名規則。

完成後至少跑一個輕量檢查，確認：

- article / figure brief / fidelity 三檔存在。
- article 正文繁中漢字數或非空白字數足夠初稿要求。
- 無 HTML tag。
- 無 U+2014 / U+2015 em dash。
- 除 frontmatter 外無正文 `---` divider。
- 配圖方案不是空泛圖片標題，而是包含目的、圖型、畫面結構、文字元素、風格、避免事項。

### 實戰補充：artifact-level QC（2026-06）

Transcript-led 模式通常一次交付 article / figure brief / fidelity 三檔；QC 不要只檢 article。尤其 fidelity 標題或 figure brief 的說明文字很容易殘留 em dash。final response 前用一個小型 Python 檢查三檔：

```bash
python3 - <<'PY'
from pathlib import Path
import re
article = Path('<workspace>/articles/<slug>-analysis.md')
figure = Path('<workspace>/figures/<slug>-figure-brief.md')
report = Path('<workspace>/reports/<slug>-fidelity.md')
text = article.read_text()
body = text.split('---', 2)[2] if text.startswith('---') else text
print('files_exist:', all(p.exists() for p in [article, figure, report]))
print('article_cjk_chars:', len(re.findall(r'[\u4e00-\u9fff]', body)))
print('article_nonspace_chars:', len(re.findall(r'\S', body)))
print('article_html_tags:', len(re.findall(r'<[^>]+>', text)))
print('article_em_dash:', sum(1 for ch in text if ch in '\u2014\u2015'))
print('all_em_dash:', sum(1 for p in [article, figure, report] for ch in p.read_text() if ch in '\u2014\u2015'))
print('article_h1_lines:', [i+1 for i,l in enumerate(text.splitlines()) if l.startswith('# ')])
print('article_divider_lines:', [i+1 for i,l in enumerate(text.splitlines()) if l.strip() == '---'])
print('figure_keys:', re.findall(r'image_key: `([^`]+)`', figure.read_text()))
print('fidelity_evidence_rows:', len(re.findall(r'^\\| \\d+ \\|', report.read_text(), flags=re.M)))
PY
```

回覆使用者時只列檢查摘要與 caveat，不貼整篇長文。若只是初稿交付，明確說「未跑 Gemini 視覺分析、未插入真實截圖、未發布 Notion」。


## 何時升級回完整 v2a

以下任一情況必須回到完整 v2a pipeline：

- 使用者要求正式發佈、Notion 上傳、Obsidian 同步。
- 使用者要求實際影片截圖 / GIF / contact sheet。
- 文章需要引用畫面細節而 transcript 無法支持。
- 需要驗證封面圖或影片中的 UI / 投影片內容。