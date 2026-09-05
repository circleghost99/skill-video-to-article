# Tool-comparison video research

Use this reference when a YouTube video compares coding agents, AI products, model harnesses, or developer tools through a hands-on build.

## Evidence separation

Keep three evidence layers separate in notes and final prose:

1. **Video-observed**: facts visible in the recording, such as the generated app UI, comparison table, test dashboard, or live interaction.
2. **Transcript-reported**: claims stated by the presenter, especially cost, token, elapsed-time, sub-agent, and tool-call numbers.
3. **Officially documented**: current product positioning and documented capabilities from first-party docs.

Do not silently upgrade a presenter claim into an independent benchmark. If a number appears both in narration and a screenshot, still record the exact source and note any mismatch.

## Experimental validity checks

Before writing a winner/loser conclusion, record:

- model/version and harness used on each side;
- prompt and whether the prompt contains explicit planning, scope, stop conditions, and acceptance criteria;
- execution time, token/cost budget, parallel-agent policy, tool-call limits, and permissions;
- what "done" meant for each run;
- output quality dimensions: UX/product judgment, architecture, reliability, tests, speed, and cost.

A single run should be framed as a case study, not a universal ranking. If the presenter reports inconsistent values, preserve the inconsistency and use approximate language rather than silently selecting the cleanest number.

## Translating results into actionable strengths

Do not describe a tool as globally better. Map observed strengths to task shape:

- **Ambiguous product exploration**: product judgment, prioritization, UX, and scope control.
- **Explicit implementation and hardening**: architecture, edge cases, testing, security, migration, concurrency, and operational reliability.
- **Combined workflow**: use one agent to explore and shape the product, then another to audit, test, and harden it, with an external acceptance rubric.

Official docs can corroborate a tool's intended surface and workflow, but they cannot prove the video experiment's comparative outcome. Put official links next to the claim they support, not only in a trailing Sources list.

## Common pitfalls

- Do not equate more features, tests, agents, or tool calls with a better product.
- Do not equate a faster finish with higher reliability; inspect what was actually tested and what remained buggy.
- Do not present cost arithmetic from a video as precise when narration, screenshots, or later corrections disagree.
- Do not treat a high-level prompt as equally informative for every harness. Missing planning, scope, and stop criteria may advantage one tool's default behavior.
- When visual analysis returns descriptions that conflict with the transcript, verify the actual frame before making a visual claim. Keep "visually verified" distinct from "inferred from narration."

## Minimum output structure

1. What the experiment actually tested.
2. What the presenter observed in each output.
3. Where each tool was stronger, by task shape.
4. Why the result is not a universal benchmark.
5. A practical routing rule and, when appropriate, a complementary two-agent workflow.
