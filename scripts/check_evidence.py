#!/usr/bin/env python3
"""Mechanical evidence check for a Karpathy-style LLM wiki.

Report-only; never modifies files. Two sweeps:

1. Fidelity — extract candidate literals (numbers, ISO dates, direct
   quotes) from each wiki article and verify that each candidate appears
   verbatim in the raw files linked by that article's Raw field. Misses
   are listed as suspects. Derived values, product names, and deliberate
   paraphrases will show up as suspects; judging them is the reader's
   job, not this script's.
2. Inventory — list raw files that no article's Raw field references,
   excluding files whose ingest was logged as "no material".

Usage: check_evidence.py [wiki-root] [article.md ...]
Defaults: wiki-root is the current directory; all wiki/**/*.md articles
except index.md and log.md are checked.
"""

import re
import sys
from pathlib import Path

NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?\s?[KMB%]")
PLAIN_NUMBER_RE = re.compile(r"\d[\d,]{1,}")
DATE_RE = re.compile(r"\d{4}-\d{2}(?:-\d{2})?")
QUOTE_RES = [re.compile(r'"([^"\n]{15,})"'), re.compile(r"“([^”\n]{15,})”")]
METADATA_RE = re.compile(r"^>\s*(Sources?|Raw|Collected|Published|Updated):")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
FENCED_CODE_RE = re.compile(r"```.*?```", re.DOTALL)
RAW_LINK_RE = re.compile(r"\(([^)]+\.md)[^)]*\)")
NO_MATERIAL_RE = re.compile(r"no material:\s*(\S+)")
WS_RE = re.compile(r"\s+")

SKIP_FILES = {"index.md", "log.md"}


def normalize(text: str) -> str:
    return WS_RE.sub(" ", text).strip()


def strip_noise(text: str) -> str:
    text = FENCED_CODE_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(" ", text)
    text = LINK_RE.sub(r"\1", text)
    return text


def extract_candidates(text: str) -> list[str]:
    candidates = []
    for line in text.splitlines():
        if METADATA_RE.match(line.strip()):
            continue
        line = strip_noise(line)
        candidates.extend(m.group(0) for m in DATE_RE.finditer(line))
        candidates.extend(m.group(0) for m in NUMBER_RE.finditer(line))
        candidates.extend(
            m.group(0) for m in PLAIN_NUMBER_RE.finditer(line) if "," in m.group(0)
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


def iter_articles(wiki_dir: Path):
    for path in sorted(wiki_dir.rglob("*.md")):
        if path.name not in SKIP_FILES:
            yield path


def check_article(article: Path) -> list[str]:
    text = article.read_text(encoding="utf-8")
    raws = []
    for link in raw_links_of(text):
        target = (article.parent / link).resolve()
        if target.is_file():
            raws.append(normalize(target.read_text(encoding="utf-8")))
    if not raws:
        return []
    misses = []
    for cand in extract_candidates(text):
        needle = normalize(cand)
        if not any(needle in raw for raw in raws):
            misses.append(cand)
    return misses


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

    if len(argv) > 2:
        articles = [Path(a) for a in argv[2:]]
    else:
        articles = list(iter_articles(wiki_dir))

    print("# Evidence check\n")
    print("## Fidelity suspects")
    suspect_count = 0
    for article in articles:
        misses = check_article(article)
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

    print("\n## Unreferenced raw files")
    orphans = unreferenced_raws(root)
    for path in orphans:
        print(f"- {path}")
    if not orphans:
        print("(none)")

    print(f"\n## Summary\n{suspect_count} fidelity suspect(s), {len(orphans)} unreferenced raw file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
