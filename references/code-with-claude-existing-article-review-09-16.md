# Code with Claude London 2026 existing-article review notes — articles 09–16

Session-specific notes for the class-level `conference-batch-existing-article-review.md` mode. Use as a worked example when reviewing already-written conference articles against transcripts and producing deep-reading + terminology artifacts.

## Context

- Series workspace: `/Users/circleghost/.hermes/profiles/hamster/outputs/code-with-claude-london-2026/`
- Output directory: `reviews/deep-reading-terminology-pass/`
- Reviewed range: articles `09`–`16`
- Artifacts produced:
  - `09-building-signals-that-trade-themselves-review.md`
  - `10-picking-the-right-model-review.md`
  - `11-memory-and-dreaming-for-self-learning-agents-review.md`
  - `12-what-legal-agents-inherit-from-coding-agents-lessons-from-legora-review.md`
  - `13-how-to-get-to-production-faster-with-claude-managed-agents-review.md`
  - `14-build-a-production-ready-agent-with-claude-managed-agents-review.md`
  - `15-the-thinking-lever-review.md`
  - `16-how-lovable-vibecodes-production-software-at-scale-review.md`
  - `batch-09-16-summary.md`

## Review pattern that worked

1. Use `playlist_manifest.json` to map indices to article/transcript paths.
2. Read article + existing fidelity report first, then fetch transcript spans on demand for contested or high-value claims.
3. For each article, produce:
   - publishability verdict (`需小修` when faithful but needing nuance/terminology polish);
   - `Critical` / `Nice to have` / `Ignore` sections;
   - transcript-backed patch-ready Chinese wording for each useful addition;
   - terminology table with columns: `原文/目前用語`, `建議`, `理由`, `建議套用位置`;
   - writing-craft notes: Opening Hook, 認知階梯, 數字代價, 結尾框架.
4. Do not modify original articles, publish to Notion, or sync Obsidian unless explicitly requested.
5. Finish with a range-specific batch summary containing counts and cross-batch terminology normalization.

## Range 09–16 findings to remember

All eight articles were faithful enough for `需小修`; no Critical fidelity failures were found. The valuable work was in nuance boundaries and non-engineer terminology.

| Index | Key nuance to preserve | Primary fix type |
|---:|---|---|
| 09 | Man Group Amazon credit-card demo is a governance/workflow demo, not evidence that AI found alpha or a usable trading strategy. | Avoid demo overclaim; finance + agent governance terminology. |
| 10 | Prompt caching’s practical rule is append-only messages; dynamic timestamps in system prompts break cacheability. Context hygiene can beat complex orchestration. | Engineering hygiene made patch-ready. |
| 11 | Memory architecture has three layers: storage, structure, Claude-driven processing. Dreaming is out-of-band/batch work, not hot-path memory stuffing. | Architecture framework + terminology. |
| 12 | Legal/coding parallels are an example of broader knowledge-work reuse, translate, invent patterns — not a one-off legal special case. | Generalize vertical-agent lesson. |
| 13 | “Hours to quarters of work” is a future-facing capability-curve framing, not a stable present-day promise. Enterprise blockers are identity, permissions, resume-ability, and multi-agent boundaries. | Separate vision from current production constraints. |
| 14 | Managed Agents expose pick-and-choose primitives; they are not an all-or-nothing Anthropic black box. | Product positioning + API terminology. |
| 15 | Thinking lever matters because test-time compute extends task horizon; Meter/Mythos numbers (about 16 human-work hours at 50% accuracy) strengthen the article. | Add time-scale numeric evidence. |
| 16 | Lovable is not only for non-engineers; many engineers/founders also move up to specification-level work as abstraction layers improve. | Add counterintuitive audience/abstraction point. |

## Batch summary conventions

For this mode, a good summary includes:

- scope and exact output directory;
- explicit statement that original articles were not modified;
- total counts, e.g. `critical_count = 0`, `nice_to_have_count = 16`, `terminology_count = 114`;
- per-article priority table;
- cross-batch terminology strategy.

For a range like 09–16, useful cross-batch terms included:

- `eval` → `評測機制（eval）`
- `private eval` → `自家小型評測（private eval）`
- `context window` → `上下文視窗（context window）`
- `context hygiene` → `上下文清潔度（context hygiene）`
- `prompt caching` → `提示快取（prompt caching）`
- `skills` → `技能包（skills）`
- `primitive` → `基礎元件（primitive）`
- `sandbox` → `沙盒環境（sandbox）` or `隔離執行環境（sandbox）`
- `credential vault` → `憑證保險庫（credential vault）`
- `thinking` / `effort level` → `思考模式（thinking）` / `投入程度（effort level）`
- `vibe coding` → `憑感覺寫程式（vibe coding）`

## Pitfalls

- When continuing after context compaction, do not assume earlier files still need to be regenerated. Verify which review files exist, then only write the requested missing range and the matching batch summary.
- If the final user ask is just “review 09–16”, do not drift into editing the source articles. Review artifacts are the deliverable.
- Use `需小修` for faithful articles that need terminology simplification or nuance; reserve `需大修` for thesis-level mismatch or materially misleading omissions.
- Transcript line references can be approximate spans, but each proposed patch should name the supporting transcript range and where it fits in the article.
