#!/usr/bin/env python3
"""Final Gate for video-to-article outputs.

This script performs deterministic normalization and blocking checks before a
video-to-article draft can be published.

Default behavior intentionally writes normalization back to the article file:
- Simplified Chinese / non-Taiwan terms -> Taiwan Traditional Chinese
- U+2014 / U+2015 dashes -> full-width comma
- Duplicate full-width commas -> single full-width comma

Exit codes:
- 0: passed
- 1: gate failed, errors printed to stdout
- 2: usage / file error
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple


DASH_TRANSLATION = str.maketrans({"\u2014": "，", "\u2015": "，"})
HTML_TAG_RE = re.compile(r"</?[A-Za-z][^>\n]{0,200}>")
ZH_EN_STICKY_RE = re.compile(
    r"[\u4e00-\u9fff][A-Za-z][A-Za-z0-9_+-]*(?:-[A-Za-z0-9_+-]+)*"
    r"|[A-Za-z][A-Za-z0-9_+-]*(?:-[A-Za-z0-9_+-]+)*[\u4e00-\u9fff]"
)


def ensure_package(import_name: str, pip_name: str) -> None:
    if importlib.util.find_spec(import_name) is not None:
        return
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "--user", "--break-system-packages", pip_name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def build_tw_converter():
    ensure_package("zhtw", "zhtw")
    ensure_package("opencc", "opencc-python-reimplemented")

    try:
        from zhtw import convert  # type: ignore

        def zhtw_to_tw(s: str) -> str:
            return convert(s)

    except ImportError:
        from zhtw import Matcher, convert_text, load_dictionary  # type: ignore

        matcher = Matcher(load_dictionary())

        def zhtw_to_tw(s: str) -> str:
            out, _ = convert_text(s, matcher, fix=True)
            return out

    from opencc import OpenCC  # type: ignore

    opencc_s2tw = OpenCC("s2tw")

    def to_tw(s: str) -> str:
        # zhtw first keeps Taiwan terms such as 軟體 / 最佳化 / 使用者.
        # OpenCC s2tw then catches residual simplified chars zhtw 3.4.0 can miss
        # such as 续 -> 續.
        return opencc_s2tw.convert(zhtw_to_tw(s))

    return to_tw


def normalize_text(text: str) -> Tuple[str, List[str]]:
    messages: List[str] = []
    to_tw = build_tw_converter()

    converted = to_tw(text)
    if converted != text:
        text = converted
        messages.append("zhtw/opencc: converted simplified / non-TW terms to Taiwan Traditional Chinese")

    normalized = text.translate(DASH_TRANSLATION)
    normalized = re.sub(r"，{2,}", "，", normalized)
    if normalized != text:
        text = normalized
        messages.append("dash: normalized U+2014/U+2015 and collapsed duplicate full-width commas")

    return text, messages


def frontmatter_end(lines: Sequence[str]) -> Optional[int]:
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return idx
    return None


def body_line_numbers(lines: Sequence[str], fm_end: Optional[int]) -> Iterable[Tuple[int, str]]:
    start = fm_end + 1 if fm_end is not None else 0
    for idx in range(start, len(lines)):
        yield idx + 1, lines[idx]


def non_code_body_text(lines: Sequence[str], fm_end: Optional[int]) -> str:
    chunks: List[str] = []
    in_code = False
    for _, line in body_line_numbers(lines, fm_end):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith("!["):
            continue
        chunks.append(line)
    return "\n".join(chunks)


def find_body_dividers(lines: Sequence[str], fm_end: Optional[int]) -> List[str]:
    errors: List[str] = []
    allowed = {1}
    if fm_end is not None:
        allowed.add(fm_end + 1)
    for i, line in enumerate(lines, 1):
        if line.strip() == "---" and i not in allowed:
            errors.append(f"body divider line {i}")
    return errors


def find_continuous_images(lines: Sequence[str], fm_end: Optional[int]) -> List[str]:
    body_start_idx = fm_end + 1 if fm_end is not None else 0
    imgs = [idx for idx in range(body_start_idx, len(lines)) if lines[idx].strip().startswith("![")]
    errors: List[str] = []
    for a, b in zip(imgs, imgs[1:]):
        between = lines[a + 1 : b]
        has_text_between = any(x.strip() and not x.strip().startswith("![") for x in between)
        if not has_text_between:
            errors.append(f"continuous images L{a + 1} / L{b + 1}")
    return errors



def find_zh_en_spacing_issues(text: str) -> List[str]:
    matches = ZH_EN_STICKY_RE.findall(text)
    if not matches:
        return []
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            unique.append(m)
    return [f"zh-en spacing issue: {m[:80]}" for m in unique]


def run_gate(article: Path, write: bool = True) -> Tuple[int, List[str], List[str]]:
    if not article.exists() or not article.is_file():
        return 2, [], [f"file not found: {article}"]

    text = article.read_text(encoding="utf-8")
    normalized_text, messages = normalize_text(text)
    if write and normalized_text != text:
        article.write_text(normalized_text, encoding="utf-8")

    lines = normalized_text.splitlines()
    fm_end = frontmatter_end(lines)
    body_text = non_code_body_text(lines, fm_end)

    errors: List[str] = []
    errors.extend(find_body_dividers(lines, fm_end))
    errors.extend(find_continuous_images(lines, fm_end))

    if HTML_TAG_RE.search(normalized_text):
        errors.append("html tag")
    if "\u2014" in normalized_text or "\u2015" in normalized_text:
        errors.append("dash residue")

    errors.extend(find_zh_en_spacing_issues(body_text))

    if errors:
        return 1, messages, errors
    return 0, messages, []


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run video-to-article Final Gate on article_draft.md")
    parser.add_argument("article", help="Path to article_draft.md")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Run checks without writing normalization back to the article",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    article = Path(args.article).expanduser().resolve()
    try:
        code, messages, errors = run_gate(article, write=not args.check_only)
    except Exception as exc:  # Keep CLI failure explicit for agents.
        print(f"final gate error: {exc}")
        return 2

    for message in messages:
        print(message)
    if code == 0:
        print("OK: final article gate passed")
    else:
        print("\n".join(errors))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
