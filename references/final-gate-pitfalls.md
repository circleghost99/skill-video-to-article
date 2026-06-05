# final_gate.py 坑點紀錄

## 已知 false positive: body 中間的 `---`

**問題**：`final_gate.py` 的 `find_body_dividers()` 將 `---` 的允許位置鎖定在：
1. frontmatter 結尾（`---` 後直接換行進入 YAML frontmatter）
2. body 第一行（`---` 後緊接第一個 H2 或文字）

正文中間的 `---`（例如用於分隔正文與倉鼠碎碎念）會被錯誤阻擋。

**觸發情境**：寫作時在正文內插入 `---` 做視覺分隔，例如：
```markdown
...段落結尾

---

## 倉鼠碎碎念

內容...
```

**解法**：
1. **不要在 body 中間使用 `---` 分隔線**。倉鼠碎碎念本身已是 `## H2` 標記，視覺上已足夠分隔。
2. 若確實需要分隔，用 `***`（三個星號）或直接省略。

**日後修復方向**：`find_body_dividers` 的 allow-list 應擴展至支援 body 中間的 `---`，條件是：
- `---` 前後都有實際內容行（非空白行）
- `---` 之後緊接 H2 標題（`## ` 開頭）

---

## 已知 normalization side effect: 技術文章常用詞被轉得太硬

**問題**：`final_gate.py` 會用 `zhtw` / OpenCC 做台灣用語與簡繁 normalization。它能清掉很多簡體殘留，但在技術解讀文中偶爾會把自然中文改得不順，例如：
- `文件` → `檔案`（在「壓力測試文件」「寫長文件」語境會變生硬）
- `範式` → `正規化`（「產品管理範式」會變成錯義的「產品管理正規化」）
- `對象` / `類型` / `優化` 等詞可能被轉成較硬的台灣電腦術語

**觸發情境**：AI / PM / 組織文化文章，常寫到 doc、文件文化、paradigm、object、optimization 等概念；正式 gate 寫回後，局部詞彙可能需要人工順稿。

**解法**：
1. 草稿階段盡量改用較不會被誤轉的寫法，例如「草稿」「doc」「長文」「方法論」「典範」「改進對象」「優化方向」。
2. 跑正式 gate 後，用全文搜尋檢查 `正規化`、`檔案`、`物件`、`型別`、`最佳化`、`不是隻`、`分佈` 等詞是否語境自然。
3. 若為純草稿交付，可在 gate 後做小幅人工順稿，並至少重跑自訂格式檢查（frontmatter、H1、HTML、body divider、em dash、圖片）確認沒有破壞格式。

---

## 驗證方式

```bash
# 快速檢查（只讀不解）
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/final_gate.py /path/to/article.md --check-only

# 正式檢查 + 寫回 normalization
python3 /Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/final_gate.py /path/to/article.md
```