# Code with Claude London 2026 existing-article review notes — articles 17–24

Session-specific notes for the class-level `conference-batch-existing-article-review.md` mode. Use as a worked example when reviewing already-written conference articles against transcripts and producing deep-reading + terminology artifacts for a later range in the same series.

## Context

- Series workspace: `/Users/circleghost/.hermes/profiles/hamster/outputs/code-with-claude-london-2026/`
- Output directory: `reviews/deep-reading-terminology-pass/`
- Reviewed range: articles `17`–`24`
- Artifacts produced:
  - `17-building-ai-native-at-enterprise-scale-monday-com-doctolib-and-delivery-hero-review.md`
  - `18-from-one-person-to-80-scaling-a-hypergrowth-engineering-org-with-claude-code-review.md`
  - `19-build-a-proactive-agent-workflow-with-claude-code-review.md`
  - `20-build-ai-agents-using-claude-in-microsoft-foundry-review.md`
  - `21-coding-is-no-longer-the-constraint-scaling-devex-to-teams-and-agents-at-spotify-review.md`
  - `22-ai-with-claude-on-aws-from-code-to-orchestration-review.md`
  - `23-stop-babysitting-your-agents-review.md`
  - `24-what-s-new-in-claude-code-review.md`
  - `batch-17-24-summary.md`

## Review pattern that worked

1. Use `playlist_manifest.json` to map requested indices to article/report/transcript paths.
2. Read each existing article and fidelity report, then fetch transcript spans only where fidelity, terminology, or nuance needs evidence.
3. Produce one review artifact per article with this shape:
   - publishability verdict (`是` / `需小修`);
   - `Critical` / `Nice to have` / `Ignore` sections;
   - transcript-backed, patch-ready Chinese wording for each proposed addition;
   - terminology table with columns: `原文/目前用語`, `建議`, `理由`, `建議套用位置`;
   - writing-craft notes: Opening Hook, 認知階梯, 數字代價, 結尾框架.
4. Do not modify original article drafts, publish to Notion, or sync Obsidian unless the user explicitly asks for that second phase.
5. Finish with a range-specific batch summary containing priority table, counts, shared terminology strategy, and any transcript-source caveats.

## Range 17–24 findings to remember

Overall, the articles were publishable with light editorial fixes. The only `Critical` item was a denominator/interpretation clarification in #17; most other work was terminology and nuance.

| Index | Key nuance to preserve | Primary fix type |
|---:|---|---|
| 17 | Delivery Hero's HeroGen `85% success rate` means accepted/merged generated PRs relative to actively rejected PRs, not total Jira-ticket-to-production automation. Doctolib's monolith lesson is that Claude learns old patterns unless teams label the new standard. | Prevent metric overclaim; enterprise-agent terminology. |
| 18 | Base44's evals evolved from simple frustration signals in chat to user simulation and CI/CD-style validation of generated apps. The team-size story is about moving bottlenecks, not magic staffing. | Eval strategy and org-scaling framing. |
| 19 | Claude Code Routines are a managed automation surface defined by prompt, repositories, connectors, and trigger; emphasize steerability and agent-on-agent review rather than treating routines as generic cron. | Product framing + non-engineer explanation. |
| 20 | Microsoft Foundry should read as a unified production platform for AI apps/agents with governance, security, observability, deployment, 1,400+ connectors, and MCP tools — not merely a prototype demo surface. Fix any stray wording like `接程式式` → `接進程式`. | Enterprise-cloud terminology + typo/wording pass. |
| 21 | The original manifest transcript was noisy speaker metadata; use `transcripts/retranscribe/21-spotify-en.lines.txt`. Preserve Spotify numbers: ~3,000 engineers, ~4,500 daily deploys, >99% weekly AI tool usage, 94% self-reported productivity lift, 76% more PRs, 2.5M automated maintenance PRs, Hyrum's Law, Honk, Chirp, shared sessions. | Transcript-source fallback + metric preservation. |
| 22 | Keep Bedrock APIs, Claude platform on AWS, and Claude desktop/workshop usage distinct. Bedrock covers model choice plus evals, prompt optimization, grounding, guardrails, PII masking, and agent execution. | Cloud/platform distinction + lifecycle terminology. |
| 23 | The thesis is not “let agents interrupt humans more”; it is that Claude should earn human attention and background routines reduce babysitting. Skills can function as self-improving/shared memory. | Thesis clarity + agent UX terminology. |
| 24 | Auto mode is a safety/productivity tradeoff with a workaround path; native worktree support, multi-agent code review, routines research preview, and agent view/remote control are workflow-control features, not just a feature list. | Safety logic + product terminology. |

## Batch summary conventions reinforced by this range

A good batch summary for later ranges should include:

- exact reviewed indices and output directory;
- explicit statement that original articles were not modified;
- per-article table with publishability, `critical_count`, `nice_to_have_count`, `terminology_count`, and priority;
- P0/P1/P2 action order, where P0 is reserved for materially misleading claims;
- cross-batch terminology normalization list;
- transcript caveats, especially when a manifest transcript is corrupted and an alternate transcript was used.

For 17–24, useful cross-batch terms included:

- `evals` → `評測機制（evals）`
- `context` → `上下文資料（context）`
- `MCP` → `模型上下文協議（MCP）`
- `production` → `正式上線環境（production）`
- `routine` → `routine（雲端例行任務）`
- `worktrees` → `隔離工作樹（worktrees）`
- `observability` → `可觀測性（observability）`
- `governance` → `治理機制（governance）`
- `prompt injection` → `提示注入攻擊（prompt injection）`

## Pitfalls

- When a manifest transcript looks corrupted or content-free, do not force the review from it. Search the same workspace for retranscribed alternatives, document the alternate source in the review, and avoid treating the noisy transcript as evidence.
- Do not count a markdown terminology table with a bullet-only parser; terminology rows are table rows in this mode. If validating counts, parse both table rows and bullet formats.
- After context compaction, do not regenerate already-written reviews. Verify existing range files and only add missing summaries or the next requested range.
- Keep review artifacts separate from source article edits. If the user later asks to apply fixes, treat that as a separate edit pass using the review files as the patch plan.
