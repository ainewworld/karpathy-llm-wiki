#!/usr/bin/env python3
"""Mechanical evidence check for a Karpathy-style LLM wiki.

Report-only; never modifies files. Three sweeps:

1. Fidelity — extract candidate literals (specific numbers, ISO dates,
   direct quotes) from each wiki article and verify that each candidate
   appears verbatim in the body of the raw files linked by that
   article's Raw field. Misses are listed as suspects. Derived values,
   product names, and deliberate paraphrases will show up as suspects;
   judging them is the reader's job, not this script's.
2. Evidence errors — articles that cannot be verified at all: a missing
   Raw field on a non-archive article, Raw links that do not resolve,
   or Raw links that escape raw/ (evidence must live in immutable raw/).
3. Inventory — raw files that no article's Raw field references,
   excluding files whose ingest was logged as "no material".

Coverage boundary (closed candidate set, frozen): candidates are
- quotes of 15+ characters (double-quoted spans and body blockquotes)
- ISO dates (YYYY-MM-DD, YYYY-MM)
- specific numbers: thousands-grouped (10,000), dotted (2.1.80, 3.14),
  suffixed (42K, 99.9%), or 4+ digits (2026)
Small plain integers ("42", "500") and exotic forms (signs, currencies,
spelled-out dates) are deliberately not checked; they belong to the
compile-time locate-before-write rule and to judgment review. New prose
forms extend this list in the docstring, not the regexes.

The exit code carries no information; the report is the interface.

Usage: check_evidence.py [project-root] [article.md ...]
Defaults: project-root is the current directory; all wiki/**/*.md
articles except index.md and log.md are checked. Article paths may be
absolute or relative to the project root.
"""

import re
import sys
from pathlib import Path

NUMBER_TOKEN_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)*\s*[KMB%]?|\d+(?:\.\d+)*\s*[KMB%]?")
SUFFIX_RE = re.compile(r"[KMB%]$")
DATE_RE = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")
QUOTE_RES = [re.compile(r'"([^"\n]*)"'), re.compile(r"“([^”\n]*)”")]
SPACED_SUFFIX_RE = re.compile(r"\s+([KMB%])$")
METADATA_RE = re.compile(r"^>\s*(Sources?|Raw|Collected|Published|Updated|Archived):")
STATUS_LINE_RE = re.compile(r"^>\s*\*\*Status:")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
RAW_LINK_RE = re.compile(r"\(([^)]+\.md)[^)]*\)")
NO_MATERIAL_HEADING_RE = re.compile(
    r"^## \[[^\]]*\]\s*ingest\s*\|\s*no material:\s*(\S+)", re.IGNORECASE
)
ARCHIVED_RE = re.compile(r"^>\s*Archived:")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
WS_RE = re.compile(r"\s+")

SKIP_FILES = {"index.md", "log.md"}


def normalize(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def split_header(lines: list[str]) -> tuple[list[str], list[str]]:
    """Split lines into the metadata header (the contiguous blockquote
    block right after the H1) and everything else. Only the header may
    carry metadata semantics; identical lines in the body are content."""
    i = 0
    while i < len(lines) and not lines[i].startswith("# "):
        i += 1
    if i >= len(lines):
        return [], lines
    i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    header = []
    while i < len(lines) and lines[i].strip().startswith(">"):
        header.append(lines[i])
        i += 1
    return header, lines[i:]


def strip_fences(text: str) -> str:
    """Remove fenced code blocks (3+ backticks or tildes, closed by a
    fence of the same character and at least the same length)."""
    out = []
    fence_char = None
    fence_len = 0
    for line in text.splitlines():
        m = FENCE_RE.match(line)
        if fence_char:
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len:
                fence_char = None
            continue
        if m:
            fence_char = m.group(1)[0]
            fence_len = len(m.group(1))
            continue
        out.append(line)
    return "\n".join(out)


def strip_noise(text: str) -> str:
    text = INLINE_CODE_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    return text


def keep_number(token: str) -> bool:
    token = token.strip()
    if SUFFIX_RE.search(token) or "," in token or "." in token:
        return True
    return len(token) >= 4


def extract_candidates(text: str) -> list[tuple[str, bool]]:
    """Return (candidate, is_quote) pairs. Quote candidates are checked
    as substrings; everything else uses boundary matching."""
    text = strip_fences(text)
    header, body = split_header(text.splitlines())
    candidates: list[tuple[str, bool]] = []
    skip_status_block = False
    blockquote: list[str] = []

    def flush_blockquote():
        if blockquote:
            joined = normalize(" ".join(blockquote))
            if len(joined) >= 15:
                candidates.append((joined, True))
            blockquote.clear()

    for line in [l for l in header if not METADATA_RE.match(l.strip())] + body:
        stripped = line.strip()
        if STATUS_LINE_RE.match(stripped):
            flush_blockquote()
            skip_status_block = True
            continue
        if skip_status_block:
            if stripped.startswith(">"):
                continue
            skip_status_block = False
        if stripped.startswith(">"):
            blockquote.append(stripped.lstrip(">").strip())
            continue
        flush_blockquote()
        line = strip_noise(line)
        candidates.extend((m.group(0), False) for m in DATE_RE.finditer(line))
        candidates.extend(
            (m.group(0), False) for m in NUMBER_TOKEN_RE.finditer(line) if keep_number(m.group(0))
        )
        for quote_re in QUOTE_RES:
            candidates.extend(
                (m.group(1), True) for m in quote_re.finditer(line) if len(m.group(1).strip()) >= 15
            )
    flush_blockquote()
    seen = set()
    unique = []
    for cand, is_quote in candidates:
        cand = SPACED_SUFFIX_RE.sub(r"\1", cand.strip().strip(".,;:()[]"))
        if cand and (cand, is_quote) not in seen:
            seen.add((cand, is_quote))
            unique.append((cand, is_quote))
    return unique


def raw_links_of(article_text: str) -> list[str]:
    """Raw links come only from the metadata header; identical lines in
    the body or in code fences are content, not fields."""
    header, _ = split_header(strip_fences(article_text).splitlines())
    links = []
    for line in header:
        if re.match(r"^>\s*Raw:", line.strip()):
            links.extend(RAW_LINK_RE.findall(line))
    return links


def contains(haystack: str, needle: str, is_quote: bool) -> bool:
    if is_quote:
        return needle in haystack
    # The value must stand on its own: not part of a longer number
    # (142K must not pass for 42K), but sentence-final punctuation
    # after it is fine (raw "hit 42K." must pass for 42K).
    pattern = r"(?<![\d.,])" + re.escape(needle) + r"(?!\d|[.,]\d|[KMB%])"
    return re.search(pattern, haystack) is not None


def source_content(path: Path) -> str:
    """Raw file body with the metadata header removed. Collection
    metadata (Source/Collected/Published) is bookkeeping, not evidence;
    letting it match candidates would false-pass dates and years."""
    lines = path.read_text(encoding="utf-8").splitlines()
    _, body = split_header(lines)
    return normalize("\n".join(body))


def check_article(article: Path, root: Path) -> tuple[list[str], list[str]]:
    """Return (fidelity suspects, evidence errors) for one article."""
    text = article.read_text(encoding="utf-8")
    links = raw_links_of(text)
    if not links:
        header, _ = split_header(text.splitlines())
        if any(ARCHIVED_RE.match(line.strip()) for line in header):
            return [], []
        return [], ["article has no Raw field"]
    raw_root = (root / "raw").resolve()
    raws = []
    errors = []
    for link in links:
        target = (article.parent / link).resolve()
        if not target.is_relative_to(raw_root):
            errors.append(f"Raw link escapes raw/: {link}")
        elif not target.is_file():
            errors.append(f"unresolvable Raw link: {link}")
        else:
            raws.append(source_content(target))
    misses = []
    if raws:
        for cand, is_quote in extract_candidates(text):
            needle = normalize(cand)
            if not any(contains(raw, needle, is_quote) for raw in raws):
                misses.append(cand)
    return misses, errors


def iter_articles(wiki_dir: Path):
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.relative_to(wiki_dir).as_posix() not in SKIP_FILES:
            yield path


def no_material_paths(log_file: Path) -> set[str]:
    if not log_file.is_file():
        return set()
    paths = set()
    for line in log_file.read_text(encoding="utf-8").splitlines():
        m = NO_MATERIAL_HEADING_RE.match(line)
        if m:
            paths.add(m.group(1).strip("`,;."))
    return paths


def referenced_raws(root: Path) -> set[Path]:
    referenced = set()
    for article in iter_articles(root / "wiki"):
        for link in raw_links_of(article.read_text(encoding="utf-8")):
            target = (article.parent / link).resolve()
            referenced.add(target)
    return referenced


def unreferenced_raws(root: Path) -> list[str]:
    raw_dir = root / "raw"
    if not raw_dir.is_dir():
        return []
    referenced = referenced_raws(root)
    disposed = no_material_paths(root / "wiki" / "log.md")
    missing = []
    for path in sorted(raw_dir.rglob("*.md")):
        if path.resolve() not in referenced and path.relative_to(root).as_posix() not in disposed:
            missing.append(path.relative_to(root).as_posix())
    return missing


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve() if len(argv) > 1 else Path.cwd()
    wiki_dir = root / "wiki"
    if not wiki_dir.is_dir():
        print(f"no wiki/ directory under {root}")
        return 1

    articles = []
    for arg in argv[2:]:
        path = Path(arg)
        if not path.is_absolute():
            path = root / path
        try:
            if path.resolve().relative_to(wiki_dir).as_posix() in SKIP_FILES:
                print(f"warning: {arg} is an index/log file, skipping", file=sys.stderr)
                continue
        except ValueError:
            pass
        if not path.is_file():
            print(f"warning: article not found: {arg}", file=sys.stderr)
            continue
        articles.append(path)
    if len(argv) <= 2:
        articles = list(iter_articles(wiki_dir))

    results = {}
    for article in articles:
        results[article] = check_article(article, root)

    def label(article: Path) -> Path:
        try:
            return article.resolve().relative_to(root)
        except ValueError:
            return article

    print("# Evidence check\n")
    print("## Fidelity suspects")
    suspect_count = 0
    for article, (misses, _) in results.items():
        if misses:
            print(f"\n{label(article)}")
            for miss in misses:
                print(f"- {miss}")
                suspect_count += 1
    if suspect_count == 0:
        print("\n(none)")

    print("\n## Evidence errors")
    error_count = 0
    for article, (_, errors) in results.items():
        if errors:
            print(f"\n{label(article)}")
            for error in errors:
                print(f"- {error}")
                error_count += 1
    if error_count == 0:
        print("(none)")

    print("\n## Unreferenced raw files")
    orphans = unreferenced_raws(root)
    for path in orphans:
        print(f"- {path}")
    if not orphans:
        print("(none)")

    print(
        f"\n## Summary\n{suspect_count} fidelity suspect(s), "
        f"{error_count} evidence error(s), {len(orphans)} unreferenced raw file(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
