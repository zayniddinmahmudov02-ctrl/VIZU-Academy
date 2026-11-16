"""app.scripts.set_admin_verification: the .env merge and the refusal rules (pure unit tests, no database, no terminal)."""

import contextlib
import io
import os
import stat
import tempfile
import unittest
from pathlib import Path

from app.scripts import set_admin_verification as tool

GOOD = "Correct-Horse_42!"


class TestMerge(unittest.TestCase):
    def test_adds_replaces_and_keeps_everything_else(self):
        base = "# comment\nDATABASE_NAME=vizu\nSECRET_KEY=abc def\n\nDEBUG=false"
        added = tool.merge_env(base, GOOD)
        self.assertEqual(added, f"{base}\n{tool.KEY}={GOOD}\n")
        replaced = tool.merge_env(f"A=1\n{tool.KEY}=old-value-here\nB=2\n{tool.KEY}=dup\n", GOOD)
        self.assertEqual(replaced, f"A=1\n{tool.KEY}={GOOD}\nB=2\n")  # one line only, order kept
        self.assertEqual(tool.merge_env("", GOOD), f"{tool.KEY}={GOOD}\n")

    def test_configured_check_never_needs_the_value(self):
        self.assertFalse(tool.is_configured("A=1\n"))
        self.assertFalse(tool.is_configured(f"{tool.KEY}=\n"))
        self.assertFalse(tool.is_configured(f"{tool.KEY}=''\n"))
        self.assertTrue(tool.is_configured(f"A=1\n{tool.KEY}={GOOD}\n"))
        self.assertFalse(tool.is_configured(f"# {tool.KEY}={GOOD}\n"))  # a comment is not a setting

    def test_only_safe_values_are_accepted(self):
        for bad in ("short", "with space in it!", "quote'inside-value", 'dq"inside-value-x', "back\\slash-value-12", "dollar$sign-value-12", "hash#sign-value-12", "new\nline-value-12", "ä" * 14, "x" * 129, ""):
            self.assertFalse(tool.is_valid(bad), repr(bad))
            with self.assertRaises(ValueError):
                tool.merge_env("A=1\n", bad)
        for good in (GOOD, "a" * 12, "x" * 128, "Pass.word:with@all+allowed=chars~12"):
            self.assertTrue(tool.is_valid(good), good)


class TestCommand(unittest.TestCase):
    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = tool.main(list(args))
        return code, out.getvalue()

    def test_dry_run_changes_nothing_and_says_what_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("A=1\n", encoding="utf-8")
            code, out = self.run_tool("--env-file", str(path))
            self.assertEqual((code, path.read_text(encoding="utf-8")), (0, "A=1\n"))
            self.assertIn("NOT set", out)

    def test_apply_without_a_terminal_is_refused_so_the_value_cannot_come_from_a_pipe_or_an_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("A=1\n", encoding="utf-8")
            code, out = self.run_tool("--env-file", str(path), "--apply")
            self.assertEqual((code, path.read_text(encoding="utf-8")), (2, "A=1\n"))
            self.assertIn("refused", out)

    def test_the_file_is_written_private_and_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("A=1\n", encoding="utf-8")
            tool._write_private(path, tool.merge_env(path.read_text(encoding="utf-8"), GOOD))
            self.assertEqual(path.read_text(encoding="utf-8"), f"A=1\n{tool.KEY}={GOOD}\n")
            if os.name != "nt":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual([p.name for p in Path(tmp).iterdir()], [".env"], "no temp file stays behind")


if __name__ == "__main__":
    unittest.main()
