# Gemini auth preflight and long-running analyzer jobs

Use this note when `video_analyzer.py` is the correct Step 02 path but the analyzer subprocess cannot see the configured Gemini credential, or when a long video approaches the foreground tool timeout.

## Safe auth preflight

Check presence without printing the credential:

```bash
python3 -c "import os; print({'GEMINI_API_KEY': bool(os.getenv('GEMINI_API_KEY')), 'GOOGLE_API_KEY': bool(os.getenv('GOOGLE_API_KEY'))})"
```

If both are false, verify only the key names in the canonical Hermes dotenv file. Never print values into terminal output or agent context.

Prefer the environment loader already used by the Hermes profile or a dotenv-aware launcher. Avoid raw shell `source ~/.hermes/.env`: dotenv files can contain values with spaces or shell-sensitive characters that are valid to an application parser but unsafe as shell syntax.

A dotenv-aware launcher pattern, when `python-dotenv` is available in the same Python environment as the analyzer:

```bash
python3 -c "
import os, subprocess
from dotenv import dotenv_values
cfg = dotenv_values(os.path.expanduser('~/.hermes/.env'))
for key in ('GEMINI_API_KEY', 'GOOGLE_API_KEY'):
    if cfg.get(key) and not os.environ.get(key):
        os.environ[key] = cfg[key]
subprocess.run([
    'python3',
    '/Users/circleghost/Desktop/開發/SKILL/video-to-article/scripts/video_analyzer.py',
    'VIDEO_SOURCE', '-o', 'analysis.json', '--strip-audio'
], check=True)
"
```

Replace `VIDEO_SOURCE` and run from the v2a working directory. If the profile has a canonical env wrapper, use that instead of copying this launcher.

## Long-run execution

Gemini File API processing and analysis can legitimately take more than ten minutes even for a roughly 25-minute video. A verified session took about 603 seconds end to end, split almost evenly between server-side file processing and model analysis.

For bounded analyzer jobs near the foreground timeout:

- start them as a tracked background process;
- enable completion notification;
- wait for the completion event rather than checking `ps`, `top`, or directory listings;
- after exit, read back a compact slice of `analysis.json`: summary, video info, key frames, GIF segments, local video path, thumbnail, model, and token/cost metadata;
- only then proceed to extraction.

## Interpretation

A first failure that says the API key is absent is an auth/setup preflight failure, not evidence that Gemini is unavailable. Once the key is correctly exported and the same command succeeds, preserve the successful path and do not encode a durable negative claim about the provider.
