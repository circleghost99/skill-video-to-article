# video-to-article eval seed set

Purpose: seed prompts for checking trigger accuracy, pipeline adherence, cross-skill handoff, and stopping behavior. These are not a full automated runner yet.

## Positive cases

### 1. Standard YouTube deep reading
- Prompt: `幫我把這支 YouTube 做成倉鼠深度解讀文章：https://youtube.com/watch?v=example`
- Expected behavior: Run the V2A pipeline from environment init through preview handoff.
- Assertions:
  - Creates todo checklist before execution.
  - Runs visual analysis / evidence frame path, not transcript-only by default.
  - Step 06 / Step 07 load `hamster-writing-craft`.
  - Step 08 stops for preview confirmation before Notion upload.

### 2. Slide-heavy talk
- Prompt: `這支簡報演講幫我解讀，重要投影片要截圖。`
- Expected behavior: Use Gemini + ffmpeg frame extraction, then visually verify valuable frames.
- Assertions:
  - Rejects empty, blurred, or transition-only frames.
  - Distinguishes visually verified frames from subtitle-only inference.
  - Does not insert screenshots mid-sentence.

### 3. Transcript-led lightweight mode
- Prompt: `我已經有 transcript 了，先寫初稿與 figure brief，不要跑視覺分析，也不要發布。`
- Expected behavior: Use transcript-led mode and label missing visual evidence honestly.
- Assertions:
  - Does not pretend frames were extracted.
  - Produces article, figure brief, and fidelity notes if requested by the mode.
  - No Notion / Cloudinary upload.

### 4. Concept figures requested after V2A draft
- Prompt: `這篇影片解讀每個 H2 再補 baoyu 概念資訊圖。`
- Expected behavior: Keep V2A evidence frames separate, then handoff concept figures to `baoyu-article-illustrator` + `hamster-image-generation`.
- Assertions:
  - Does not ask V2A to own AI image generation QA.
  - Avoids consecutive image blocks.
  - Maintains a figure manifest / insertion plan.

### 5. Publication after approval
- Prompt: `預覽 OK，可以發布 Notion。`
- Expected behavior: Handoff to `notion-upload-workflow` only after explicit approval.
- Assertions:
  - Uses `notion_hamster_push.py --file`, not `--content`.
  - Lets notion workflow handle local images → Cloudinary.
  - Does not manually duplicate Cloudinary upload inside V2A.

## Near-miss negatives

### A. Pure short summary
- Prompt: `幫我摘要這支影片，三句話就好。`
- Expected behavior: Do not trigger full V2A; answer as a summary task or ask if deep article is desired.

### B. Article writing craft analysis
- Prompt: `分析這篇文章的前言寫法。`
- Expected behavior: Use `hamster-writing-craft`, not V2A.

### C. Pure translation
- Prompt: `把這支影片字幕翻成繁中。`
- Expected behavior: Use translation/transcription workflow, not V2A deep-reading pipeline.

## Transcript review notes

When evaluating, inspect:
- Did the agent create and update todo state?
- Did it read the relevant references before each step?
- Did it visually verify frames instead of trusting model timestamps blindly?
- Did it stop at preview before publication?
- Did it correctly separate evidence frames, concept figures, and cover image ownership?
