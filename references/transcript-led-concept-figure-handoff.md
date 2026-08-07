# Transcript-led v2a with concept figures when Gemini vision is blocked

Session pattern: the user asks for a deep reading **and article illustrations**, but Gemini File API visual analysis is blocked by monthly spending cap / quota before `analysis.json` exists.

## Decision rule

Treat video evidence frames and concept figures as separate assets:

- **Blocked:** video evidence frames / GIFs. Do not describe slides, screenshots, UI frames, or write 「畫面顯示」 style claims.
- **Allowed when requested:** article concept figures that explain the written argument, planned with `creative/baoyu-article-illustrator` and generated / QA'd through `hamster-image-generation`.

This is still a transcript-led article. Be transparent in the work report that visual analysis was blocked; do not put pipeline/billing details in the public article intro.

## Workflow

1. Mark Gemini visual analysis and evidence-frame extraction as cancelled / blocked in the todo with the quota reason.
2. Continue transcript acquisition, theme map, draft, editorial review, and fidelity check.
3. In Step 07 editorial review, enforce **no Markdown images, no screenshot placeholders, no visual claims**.
4. After fidelity check, run Step 07.6 as concept-figure handoff if the user asked for 配圖:
   - Lock the target article path / title.
   - Create `illustrations/outline.md` and `illustrations/prompts/*.md`.
   - Use article-specific framework / comparison / flowchart / infographic visuals, not generic tech scenes.
   - Generate with Codex-first via `hamster-image-generation` rules.
5. Build a contact sheet and run QA before insertion.
6. Insert only PASS figures near their matching H2 / paragraph. Keep evidence-frame language out of captions / alt text.
7. Run Final Gate after image insertion and any manual terminology repair.

## QA lessons from this session

- Codex image generation may produce an image and then continue running or be killed with exit 143. Verify artifacts first: expected PNG exists, dimensions and bytes are sane, then salvage only valid artifacts instead of rerunning everything.
- If contact sheet QA finds one failed image, move that image aside with a `fail-*` suffix, patch only that prompt, and regenerate only the failed figure.
- Contact sheet filename labels are not part of the figure and should not count as English residue.
- If the figure itself contains unwanted English, e.g. a label like `AI 加速` when the image spec says no English letters, patch the prompt to a pure Chinese label such as `智能加速`, regenerate only that figure, rebuild the contact sheet, and rerun QA.
- If Codex logs show deterministic text overlay / PIL / ImageDraw attempts during a Codex-native-only task, reject that candidate and regenerate natively unless the user explicitly allows deterministic repair.

## Final response contract

Report separately:

- evidence-frame status: blocked / not used, with honest reason;
- concept-figure status: generated count, contact sheet QA result, insertion count;
- final gate result and artifact paths.
