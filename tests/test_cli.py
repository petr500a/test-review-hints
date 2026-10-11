from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from test_review_hints.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_cli(self, *args):
        output = io.StringIO()
        with redirect_stdout(output):
            status = main([str(arg) for arg in args])
        return status, output.getvalue()

    def test_missing_input_is_not_a_successful_clean_scan(self):
        status, output = self.run_cli(self.root / 'missing')
        self.assertEqual(status, 2)
        self.assertIn('INPUT', output)
        self.assertIn('incomplete', output.lower())

    def test_empty_directory_and_non_python_file_are_input_errors(self):
        empty = self.root / 'empty'
        empty.mkdir()
        text = self.root / 'notes.txt'
        text.write_text('notes', encoding='utf-8')
        for path in (empty, text):
            with self.subTest(path=path.name):
                status, output = self.run_cli(path)
                self.assertEqual(status, 2)
                self.assertIn('INPUT', output)

    def test_multiple_roots_and_overlaps_are_scanned_once(self):
        paths = []
        for name in ('one', 'two'):
            directory = self.root / name
            directory.mkdir()
            path = directory / ('test_' + name + '.py')
            path.write_text('def test_value():\n    return\n    assert False\n', encoding='utf-8')
            paths.append(path)
        status, output = self.run_cli(paths[0].parent, paths[1].parent, paths[1])
        self.assertEqual(status, 0)
        self.assertEqual(output.count(': RD '), 2)

    def test_bad_source_is_reported_while_other_files_are_scanned(self):
        (self.root / 'test_bad.py').write_text('def broken(:\n', encoding='utf-8')
        (self.root / 'test_good.py').write_text('def test_value():\n    raise RuntimeError\n    assert False\n', encoding='utf-8')
        status, output = self.run_cli(self.root)
        self.assertEqual(status, 2)
        self.assertIn('PARSE', output)
        self.assertIn(': RD ', output)

    def test_encoding_error_is_reported_and_declared_encoding_is_supported(self):
        path = self.root / 'test_encoding.py'
        path.write_bytes(b'x = "\xff"\n')
        status, output = self.run_cli(path)
        self.assertEqual(status, 2)
        self.assertIn('PARSE', output)
        path.write_bytes(b'# coding: latin-1\nx = "\xff"\n')
        status, output = self.run_cli(path)
        self.assertEqual(status, 0)
        self.assertNotIn('PARSE', output)

    def test_scanning_does_not_execute_or_change_input(self):
        marker = self.root / 'must_not_exist'
        source = 'from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n'
        path = self.root / 'test_effect.py'
        path.write_text(source, encoding='utf-8')
        before = path.read_bytes()
        status, _ = self.run_cli(path)
        self.assertEqual(status, 0)
        self.assertFalse(marker.exists())
        self.assertEqual(path.read_bytes(), before)

    def test_ambiguous_boundary_hint_requires_opt_in(self):
        path = self.root / 'test_bus.py'
        path.write_text('def test_bus():\n    bus.emit("x")\n    assert bus.get_all() == ["x"]\n', encoding='utf-8')
        status, output = self.run_cli(path)
        self.assertEqual(status, 0)
        self.assertNotIn('R43', output)
        status, output = self.run_cli('--include-boundary-hints', path)
        self.assertEqual(status, 0)
        self.assertIn('R43', output)
