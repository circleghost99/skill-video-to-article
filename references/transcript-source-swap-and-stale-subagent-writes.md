# Transcript source swap and stale subagent writes

## Trigger

Use this recovery pattern when the first transcript is later found to be duplicated, partial, wrong-language, auto-caption quality, or otherwise replaced after theme-map or writing subagents have already been dispatched.

## Risk

Background subagents keep the source state and prompt they received at dispatch time. Replacing `transcript_clean.txt` in place does not guarantee an already-running worker will reread it. An older worker can finish later and overwrite `notes_theme-map.md` or `article_draft.md` with stale line numbers and provenance. A sibling-modification warning is evidence of concurrent writers, not proof that the newest artifact won.

## Safe recovery

1. Save the accepted transcript under a versioned canonical path such as `canonical_transcript/transcript_clean.txt`.
2. Record provenance before downstream work: method, language, generated/manual status, segment count, duration coverage, character count, and preferably a SHA-256 hash.
3. Dispatch the replacement theme-map worker with the canonical absolute path and a new output path, e.g. `notes_theme-map.canonical.md`; do not let old and new workers write the same target.
4. After both jobs settle, verify the winning map header names the accepted transcript, line count, and quality. Only then atomically promote it to `notes_theme-map.md`.
5. Draft and fidelity prompts must name the canonical transcript as the only source of truth. If a draft may have started from the stale map, run fidelity against the canonical transcript and overwrite the draft before publishing.
6. Treat subagent completion summaries as unverified until the artifact is read back. Check source provenance in the file itself, not only file existence or modification time.

## Minimal acceptance gate

- transcript coverage is near full duration (normally at least 90%)
- opening, middle, and ending samples contain no rolling-caption repetition
- theme-map line references resolve against the accepted transcript
- theme map does not describe an old segment count or subtitle quality
- final fidelity log names the canonical transcript absolute path

This pattern prevents a late stale worker from silently reintroducing rejected source material.
