"""Проверки защитного режима архивирования истории перемещения."""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).with_name("archive-monster-moves.py")
SPEC = importlib.util.spec_from_file_location("archive_monster_moves", SCRIPT)
archive = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(archive)


class ArchiveMonsterMovesTest(unittest.TestCase):
    def test_dry_run_only_counts_even_when_rows_exist(self):
        with mock.patch.object(sys, "argv", [str(SCRIPT), "--before", "2026-11-01T00:00:00Z"]), \
                mock.patch.object(archive, "psql", return_value="42") as query:
            archive.main()
        self.assertEqual(query.call_count, 1)
        self.assertIn("SELECT count(*)", query.call_args.args[1])

    def test_apply_requires_archive_before_database_access(self):
        with mock.patch.object(sys, "argv", [str(SCRIPT), "--apply", "--before", "2026-11-01T00:00:00Z"]), \
                mock.patch.object(archive, "psql") as query, \
                self.assertRaises(SystemExit) as failure:
            archive.main()
        self.assertEqual(failure.exception.code, 2)
        query.assert_not_called()


if __name__ == "__main__":
    unittest.main()
