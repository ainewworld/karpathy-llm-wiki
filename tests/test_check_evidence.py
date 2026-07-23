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
Install with `--limit 9000` after downloading.

```
example 78K and 9,999
```

> **Status: Outdated** (2026-07-23)
> The forks situation changed after this was written.
"""

SECOND_RAW = """# Unrelated Notes

> Source: https://example.com/notes
> Collected: 2026-05-01
> Published: Unknown

Nothing here is compiled anywhere.
"""

BOUNDARY_RAW = """# Numbers

> Source: https://example.com/numbers
> Collected: 2026-06-01
> Published: Unknown

Ghostty reached 142K stars. Uptime was 95.5%. Forks: 13,020.
"""

BOUNDARY_ARTICLE = """# Boundary

> Sources: Example, 2026-06-01
> Raw: [numbers](../../raw/t/numbers.md)

Ghostty has 42K stars and uptime of 5.5%. Forks grew to 3,020.
"""

PLAIN_RAW = """# Plain

> Source: https://example.com/plain
> Collected: 2026-06-01
> Published: Unknown

No numeric facts here at all.
"""

PLAIN_ARTICLE = """# Plain numbers

> Sources: Example, 2026-06-01
> Raw: [plain](../../raw/t/plain.md)

There were 42 users; the ratio was 3.14; founded in 2026.
"""

ARCHIVE_ARTICLE = """# Old answer

> Sources: [Ghostty](ghostty.md)
> Archived: 2026-07-01

At the time, Ghostty had 999K stars and the maintainer said "totally made up quote here".
"""

NO_RAW_ARTICLE = """# No raw

> Sources: Example, 2026-06-01

This ordinary article forgot its Raw field and claims 999K users.
"""

BROKEN_RAW_ARTICLE = """# Broken

> Sources: Example, 2026-06-01
> Raw: [gone](../../raw/t/nonexistent.md)

Claims 999K users with no evidence anywhere.
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


def run_checker(root: Path, *args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(root), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class WikiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup


class FidelityCheckTest(WikiTestCase):
    def setUp(self):
        super().setUp()
        make_wiki(self.root)

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
        self.assertNotIn("9000", result.stdout)
        self.assertNotIn("78K", result.stdout)
        self.assertNotIn("9,999", result.stdout)

    def test_ignores_status_block_marker_date(self):
        result = run_checker(self.root)
        self.assertNotIn("2026-07-23", result.stdout)


class BoundaryMatchingTest(WikiTestCase):
    def setUp(self):
        super().setUp()
        (self.root / "raw" / "t").mkdir(parents=True)
        (self.root / "raw" / "t" / "numbers.md").write_text(BOUNDARY_RAW)
        (self.root / "wiki" / "t").mkdir(parents=True)
        (self.root / "wiki" / "t" / "a.md").write_text(BOUNDARY_ARTICLE)
        (self.root / "wiki" / "index.md").write_text("# Knowledge Base Index\n")
        (self.root / "wiki" / "log.md").write_text("# Wiki Log\n")

    def test_substring_of_larger_number_does_not_pass(self):
        result = run_checker(self.root)
        self.assertIn("42K", result.stdout)
        self.assertIn("5.5%", result.stdout)
        self.assertIn("3,020", result.stdout)


class NumberCoverageTest(WikiTestCase):
    def setUp(self):
        super().setUp()
        (self.root / "raw" / "t").mkdir(parents=True)
        (self.root / "raw" / "t" / "plain.md").write_text(PLAIN_RAW)
        (self.root / "wiki" / "t").mkdir(parents=True)
        (self.root / "wiki" / "t" / "a.md").write_text(PLAIN_ARTICLE)
        (self.root / "wiki" / "index.md").write_text("# Knowledge Base Index\n")
        (self.root / "wiki" / "log.md").write_text("# Wiki Log\n")

    def test_flags_decimals_and_long_numbers(self):
        result = run_checker(self.root)
        self.assertIn("3.14", result.stdout)
        self.assertIn("2026", result.stdout)

    def test_small_plain_integers_are_out_of_scope(self):
        result = run_checker(self.root)
        self.assertNotIn("42 users", result.stdout)
        for line in result.stdout.splitlines():
            self.assertFalse(line.strip() == "- 42", f"small int flagged: {line}")


class EvidenceErrorTest(WikiTestCase):
    def setUp(self):
        super().setUp()
        make_wiki(self.root)

    def test_archive_page_without_raw_is_legitimate(self):
        (self.root / "wiki" / "ai-research" / "old-answer.md").write_text(ARCHIVE_ARTICLE)
        result = run_checker(self.root)
        self.assertNotIn("999K", result.stdout)
        self.assertNotIn("old-answer", result.stdout)

    def test_ordinary_article_without_raw_is_an_evidence_error(self):
        (self.root / "wiki" / "ai-research" / "no-raw.md").write_text(NO_RAW_ARTICLE)
        result = run_checker(self.root)
        self.assertIn("no-raw", result.stdout)
        self.assertIn("no Raw field", result.stdout)

    def test_broken_raw_link_is_an_evidence_error(self):
        (self.root / "wiki" / "ai-research" / "broken.md").write_text(BROKEN_RAW_ARTICLE)
        result = run_checker(self.root)
        self.assertIn("broken", result.stdout)
        self.assertIn("unresolvable Raw link", result.stdout)


class CliTest(WikiTestCase):
    def setUp(self):
        super().setUp()
        make_wiki(self.root)

    def test_article_args_resolve_against_root_not_cwd(self):
        result = run_checker(self.root, "wiki/ai-research/ghostty.md", cwd="/")
        self.assertEqual(result.returncode, 0)
        self.assertIn("3,020", result.stdout)

    def test_missing_article_is_a_warning_not_a_traceback(self):
        result = run_checker(self.root, "wiki/nope.md")
        self.assertEqual(result.returncode, 0)
        self.assertIn("wiki/nope.md", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class RawInventoryTest(WikiTestCase):
    def test_reports_raw_file_never_compiled(self):
        make_wiki(self.root)
        result = run_checker(self.root)
        self.assertIn("raw/misc/notes.md", result.stdout)

    def test_no_material_disposition_suppresses_report(self):
        log = (
            "# Wiki Log\n\n"
            "## [2026-05-01] ingest | no material: raw/misc/notes.md\n"
            "- Disposition: No material\n"
        )
        make_wiki(self.root, log=log)
        result = run_checker(self.root)
        self.assertNotIn("notes.md", result.stdout)

    def test_no_material_does_not_suppress_same_name_elsewhere(self):
        (self.root / "raw" / "other").mkdir(parents=True)
        (self.root / "raw" / "other" / "notes.md").write_text(SECOND_RAW)
        log = (
            "# Wiki Log\n\n"
            "## [2026-05-01] ingest | no material: raw/misc/notes.md\n"
            "- Disposition: No material\n"
        )
        make_wiki(self.root, log=log)
        result = run_checker(self.root)
        self.assertNotIn("raw/misc/notes.md", result.stdout)
        self.assertIn("raw/other/notes.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
