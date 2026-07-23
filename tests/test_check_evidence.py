import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_evidence.py"

RAW_CONTENT = """# Ghostty Update

> Source: https://example.com/ghostty
> Collected: 2026-04-17
> Published: 2026-04-16

Ghostty reached 42K stars on GitHub in April 2026.
The maintainer said "the terminal should feel invisible to users" in the interview.
Daily active users reached 10,000 by March.
"""

ARTICLE_CONTENT = """# Ghostty

> Sources: Example, 2026-04-16
> Raw: [ghostty](../../raw/ai-research/2026-04-17-ghostty.md)

## Overview

Ghostty has 42K stars and reached 10,000 daily active users.
The maintainer said "the terminal should feel invisible to users".

## Growth

Forks grew to 3,020 last week.
Install with `--limit 500` after downloading.

```
ignore this 8888 number
```
"""

SECOND_RAW = """# Unrelated Notes

> Source: https://example.com/notes
> Collected: 2026-05-01
> Published: Unknown

Nothing here is compiled anywhere.
"""


def make_wiki(root: Path, log: str = ""):
    (root / "raw" / "ai-research").mkdir(parents=True)
    (root / "raw" / "ai-research" / "2026-04-17-ghostty.md").write_text(RAW_CONTENT)
    (root / "raw" / "misc").mkdir(parents=True)
    (root / "raw" / "misc" / "notes.md").write_text(SECOND_RAW)
    (root / "wiki" / "ai-research").mkdir(parents=True)
    (root / "wiki" / "ai-research" / "ghostty.md").write_text(ARTICLE_CONTENT)
    (root / "wiki" / "index.md").write_text("# Knowledge Base Index\n")
    (root / "wiki" / "log.md").write_text(log or "# Wiki Log\n")


def run_checker(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root), *args],
        capture_output=True,
        text=True,
    )


class FidelityCheckTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        make_wiki(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_flags_value_absent_from_raw(self):
        result = run_checker(self.root)
        self.assertIn("3,020", result.stdout)

    def test_passes_values_and_quotes_present_in_raw(self):
        result = run_checker(self.root)
        self.assertNotIn("42K", result.stdout.replace("3,020", ""))
        self.assertNotIn("10,000", result.stdout)
        self.assertNotIn("invisible to users", result.stdout)

    def test_ignores_numbers_in_code(self):
        result = run_checker(self.root)
        self.assertNotIn("500", result.stdout)
        self.assertNotIn("8888", result.stdout)


class RawInventoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_reports_raw_file_never_compiled(self):
        make_wiki(self.root)
        result = run_checker(self.root)
        self.assertIn("raw/misc/notes.md", result.stdout)

    def test_no_material_disposition_suppresses_report(self):
        log = (
            "# Wiki Log\n\n"
            "## [2026-05-01] ingest | no material: notes.md\n"
            "- Disposition: No material\n"
        )
        make_wiki(self.root, log=log)
        result = run_checker(self.root)
        self.assertNotIn("notes.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
