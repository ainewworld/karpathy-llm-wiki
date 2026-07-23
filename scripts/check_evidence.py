#!/usr/bin/env python3
"""Mechanical evidence check for a Karpathy-style LLM wiki.

Report-only; never modifies files. Three sweeps:

1. Fidelity — extract candidate literals (specific numbers, ISO dates,
   direct quotes) from each wiki article and verify that each candidate
   appears verbatim in the raw files linked by that article's Raw field.
   Misses are listed as suspects. Derived values, product names, and
   deliberate paraphrases will show up as suspects; judging them is the
   reader's job, not this script's.
2. Evidence errors — articles that cannot be verified at all: a missing
   Raw field on a non-archive article, or Raw links that do not resolve.
3. Inventory — raw files that no article's Raw field references,
   excluding files whose ingest was logged as "no material".

Coverage boundary: only specific-enough literals are candidates —
numbers with a K/M/B/% suffix, a comma, a decimal point, or 4+ digits,
plus ISO dates and quotes of 15+ characters. Small plain integers
("42", "500") are deliberately not checked; they are too common in
prose to keep the report worth reading.

Usage: check_evidence.py [project-root] [article.md ...]
Defaults: project-root is the current directory; all wiki/**/*.md
articles except index.md and log.md are checked. Article paths may be
absolute or relative to the project root.
"""

import re
import sys
from pathlib import Path

NUMBER_TOKEN_RE = re.compile(r"\d[\d,]*(?:\.\d+)?\s?[KMB%]?")
SUFFIX_RE = re.compile(r"[KMB%]$")
DATE_RE = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")
QUOTE_RES = [re.compile(r'"([^"\n]{15,})"'), re.compile(r"“([^”\n]{15,})”")]
METADATA_RE = re.compile(r"^>\s*(Sources?|Raw|Collected|Published|Updated|Archived):")
STATUS_LINE_RE = re.compile(r"^>\s*\*\*Status:")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
RAW_LINK_RE = re.compile(r"\(([^)]+\.md)[^)]*\)")
NO_MATERIAL_RE = re.compile(r"no material:\s*(\S+)")
ARCHIVED_RE = re.compile(r"^>\s*Archived:", re.MULTILINE)
WS_RE = re.compile(r"\s+")

SKIP_FILES = {"index.md", "log.md"}


def normalize(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def strip_noise(text: str) -> str:
    text = INLINE_CODE_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    return text


def keep_number(token: str) -> bool:
    token = token.strip()
    if SUFFIX_RE.search(token) or "," in token or "." in token:
        return True
    return len(token) >= 4


def extract_candidates(text: str) -> list[str]:
    text = FENCED_CODE_RE.sub(" ", text)
    candidates = []
    for line in text.splitlines():
        stripped = line.strip()
        if METADATA_RE.match(stripped) or STATUS_LINE_RE.match(stripped):
            continue
        line = strip_noise(line)
        candidates.extend(m.group(0) for m in DATE_RE.finditer(line))
        candidates.extend(
            m.group(0) for m in NUMBER_TOKEN_RE.finditer(line) if keep_number(m.group(0))
        )
        for quote_re in QUOTE_RES:
            candidates.extend(m.group(1) for m in quote_re.finditer(line))
    seen = set()
    unique = []
    for cand in candidates:
        cand = cand.strip(".,;:()[]")
        if cand and cand not in seen:
            seen.add(cand)
            unique.append(cand)
    return unique


def raw_links_of(article_text: str) -> list[str]:
    links = []
    for line in article_text.splitlines():
        if re.match(r"^>\s*Raw:", line.strip()):
            links.extend(RAW_LINK_RE.findall(line))
    return links


def contains(haystack: str, needle: str, is_quote: bool) -> bool:
    if is_quote:
        return needle in haystack
    pattern = r"(?<![\d.,])" + re.escape(needle) + r"(?![\d.,KMB%])"
    return re.search(pattern, haystack) is not None


def source_content(path: Path) -> str:
    """Raw file content minus its metadata header. Collection metadata
    (Source/Collected/Published) is bookkeeping, not evidence; letting it
    match candidates would false-pass dates and years."""
    lines = path.read_text(encoding="utf-8").splitlines()
    body = [line for line in lines if not METADATA_RE.match(line.strip())]
    return normalize("\n".join(body))


def check_article(article: Path) -> tuple[list[str], list[str]]:
    """Return (fidelity suspects, evidence errors) for one article."""
    text = article.read_text(encoding="utf-8")
    links = raw_links_of(text)
    if not links:
        if ARCHIVED_RE.search(text):
            return [], []
        return [], ["article has no Raw field"]
    raws = []
    errors = []
    for link in links:
        target = (article.parent / link).resolve()
        if target.is_file():
            raws.append(source_content(target))
        else:
            errors.append(f"unresolvable Raw link: {link}")
    misses = []
    if raws:
        quote_min_len = 15
        for cand in extract_candidates(text):
            needle = normalize(cand)
            is_quote = len(cand) >= quote_min_len and not any(ch.isdigit() for ch in cand[:2])
            if not any(contains(raw, needle, is_quote) for raw in raws):
                misses.append(cand)
    return misses, errors


def iter_articles(wiki_dir: Path):
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.name not in SKIP_FILES:
            yield path


def no_material_names(log_file: Path) -> set[str]:
    if not log_file.is_file():
        return set()
    names = set()
    for line in log_file.read_text(encoding="utf-8").splitlines():
        m = NO_MATERIAL_RE.search(line)
        if m:
            names.add(Path(m.group(1).rstrip("`.,;")).name)
    return names


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
    disposed = no_material_names(root / "wiki" / "log.md")
    missing = []
    for path in sorted(raw_dir.rglob("*.md")):
        if path.resolve() not in referenced and path.name not in disposed:
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
        if not path.is_file():
            print(f"warning: article not found: {arg}", file=sys.stderr)
            continue
        articles.append(path)
    if len(argv) <= 2:
        articles = list(iter_articles(wiki_dir))

    print("# Evidence check\n")
    print("## Fidelity suspects")
    suspect_count = 0
    for article in articles:
        misses, _ = check_article(article)
        if misses:
            label = article
            try:
                label = article.resolve().relative_to(root)
            except ValueError:
                pass
            print(f"\n{label}")
            for miss in misses:
                print(f"- {miss}")
                suspect_count += 1
    if suspect_count == 0:
        print("\n(none)")

    print("\n## Evidence errors")
    error_count = 0
    for article in articles:
        _, errors = check_article(article)
        if errors:
            label = article
            try:
                label = article.resolve().relative_to(root)
            except ValueError:
                pass
            print(f"\n{label}")
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
