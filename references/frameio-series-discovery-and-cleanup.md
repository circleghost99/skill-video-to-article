# Frame.io series discovery and cleanup

Use this reference when a Frame.io share contains multiple videos and the requested output is one deep-reading article per video with Notion publication.

## Manifest-first contract

Create a durable workspace under:

`/Users/circleghost/.hermes/profiles/hamster/outputs/<series-slug>/`

Keep `plan.md` and `series_manifest.json` at the root. Each item should include:

```json
{
  "index": 1,
  "asset_id": "verified Frame.io asset ID",
  "title": "verified asset title",
  "source_url": "verified source/share URL",
  "source_url_verified": true,
  "duration_seconds": 0,
  "status": "pending",
  "transcript_path": "...",
  "article_path": "...",
  "evidence_dir": "...",
  "notion_page_id": null,
  "notion_url": null,
  "video_deleted": false
}
```

The series cannot enter video-processing status until the ordered asset list is actually verified. A share title, folder count, HTML bundle, or guessed endpoint is not an asset inventory. If discovery is blocked, write the resolved share URL, share/folder IDs, confirmed metadata, exact error/limitation, and an empty or partial item list. Do not fabricate placeholders that look like real videos.

## Discovery recovery

1. Resolve the short URL and record the canonical share URL.
2. Prefer an authenticated browser-visible asset listing or an officially supported export/download route.
3. If an API route returns permission denied, preserve the identifiers and error, then try a legitimate authenticated route; do not interpret 403 as permanent source loss.
4. If no route is currently available, stop before downloading and report the missing access prerequisite to the user.

## Per-video lifecycle

Process the lowest-index `pending` item only:

1. Download to a temporary per-video directory.
2. Save captions, or label the output as ASR when captions are unavailable.
3. Run `video-to-article` visual analysis, extract evidence frames/GIFs, create a contact sheet, and complete delegated plus main-agent visual QA.
4. Write the article, fidelity report, and figure plan. Keep transcript-supported claims separate from personally verified visual claims.
5. Run the final text gate after the last edit. Do not publish until the article and all images pass.
6. Publish through `notion-upload-workflow`, then read back page properties and all blocks. A publish `ok=true` alone is insufficient.
7. Verify the transcript, accepted evidence manifest, article, fidelity report, and readback artifact exist and are non-empty.
8. Delete only the local video file. Record deletion timestamp/path and verify no `.mp4`, `.mov`, `.m4v`, or `.webm` remains in that temporary item workspace.
9. Mark the manifest item complete and proceed to the next index.

If a video fails, keep its local video until the blocker is resolved. Do not skip it silently or delete it. Never delete the remote Frame.io asset.

## Series closeout

Write a series QC report with totals, per-item article/transcript/evidence paths, Final Gate status, image QA status, Notion URL/readback status, deletion status, and unresolved blockers. Mark the series complete only when every item is published and locally cleaned, or explicitly marked blocked with a user-visible reason.
