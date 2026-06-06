# Conference batch existing-article review artifacts

Use this reference when the user asks to **review already-written conference/event series articles against transcripts** and produce deep-reading / terminology improvement artifacts, rather than rewrite or publish the articles.

Example trigger:
- “Review Code with Claude London 2026 articles 01-08 against transcripts and produce deep-reading + terminology improvement artifacts”

## Scope

This is an editorial QA mode for an existing series workspace. It does **not** create new articles, upload to Notion, sync Obsidian, or modify published drafts unless the user explicitly asks for edits.

Inputs usually already exist in the series manifest:
- `playlist_manifest.json`
- `articles/<NN-slug>.md`
- `transcripts/<NN-slug>.txt`
- `reports/<NN-slug>-fidelity.md`

Recommended output directory:

```text
<series_workspace>/reviews/deep-reading-terminology-pass/
  01-<slug>-review.md
  02-<slug>-review.md
  ...
  batch-<range>-summary.md
```

If that directory already contains reviews for other indices, do not overwrite unrelated files. Only write the requested range and the matching batch summary.

## Per-article review artifact shape

Each review file should be short enough to skim but specific enough to patch from. Use this structure:

```markdown
# Review — <NN> <slug>

## 一句話判斷
- 目前文章是否可發布：是 / 需小修 / 需大修
- <one concise reason>

## A. 需要補充或調整的資訊
### Critical
- 建議：<must-fix issue or “無”>
  - transcript 依據：Lxxx-Lyyy，quote/paraphrase the relevant source
  - 目前文章位置：<heading / line / paragraph>
  - 建議改法：<patch-ready Chinese wording>

### Nice to have
- 建議：<optional strengthening detail>
  - transcript 依據：Lxxx-Lyyy
  - 目前文章位置：<where it would fit>
  - 建議改法：<specific sentence/paragraph>

### Ignore / 不建議補
- <items that are true but should stay out because they dilute the article>

## B. 專有名詞白話化建議
- 原文/目前用語：<term>
  - 建議：<白話中文（English term）>
  - 理由：<why this helps readers>
  - 建議套用位置：<first occurrence / section>

## C. 寫作技藝建議
- Opening Hook / 數字敘事 / 認知階梯 / 結尾框架 observations.
```

## Batch summary shape

Write a batch summary file with:

1. output directory path;
2. table with each index, slug, publish judgment, `critical_count`, `nice_to_have_count`, `terminology_count`, and priority;
3. P0 / P1 / P2 fix list;
4. cross-batch terminology strategy;
5. overall judgment.

Priority convention:
- **P0**: factual/numeric contradiction, core sentence corruption, or obvious typo that breaks comprehension.
- **P1**: style / OpenCC / terminology consistency issue that should be fixed before polished publication.
- **P2**: optional deep-reading enrichment or terminology clarity improvement.

## Workflow

1. Read `playlist_manifest.json` first; use manifest paths as source of truth.
2. If resuming after context compaction or a prior partial pass, verify which review files already exist and only write the requested missing range plus the matching range summary; do not overwrite unrelated earlier/later review artifacts.
3. For each requested item:
   - inspect the article headings and relevant paragraphs;
   - read the existing fidelity report when present;
   - fetch transcript ranges on demand, not the whole transcript into context;
   - verify numeric claims, core thesis sentences, image captions, and product/vision boundary claims against transcript evidence;
   - scan for OpenCC artifacts or repeated characters that final gate may miss semantically.
4. Write one review markdown per item.
5. Write one batch summary markdown.
6. Verify with a lightweight script or file checks that all requested review files exist and contain the required sections.

### Worked examples / session notes

- `references/code-with-claude-existing-article-review-09-16.md` — range 09–16 example covering faithful-but-needs-polish articles, terminology tables, batch summary counts, and pitfalls around demo overclaims / future-vision language.

## Common findings to look for

- Caption/body numeric mismatch, e.g. body says 10% but image caption says 70%.
- OpenCC artifacts: `隻是` where the intended word is `只是`; `物件` where natural usage is `對象`; `許可權` where user-facing Taiwanese usage should be `權限`.
- Repeated-character corruption such as `高可用性性性性`.
- ASR normalization: transcripts may say `Cloud Code`, `Quad Code`, or `ClockCode`; normalize to `Claude Code` in review recommendations, but cite transcript line ranges transparently.
- Article omission that is true but not critical: classify as `nice_to_have`, not `critical`, unless it changes the article’s thesis or misleads readers.

## Delivery

Final response should be concise:
- say artifacts were produced;
- list output directory and files;
- highlight P0/P1 issues;
- state that original articles / Notion / Obsidian were not modified unless explicitly done.
