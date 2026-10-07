from pathlib import Path
import tempfile
import unittest

from test_review_hints.rules import scan_file


class RulesTests(unittest.TestCase):
    def test_absolute_db_path(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test_demo.py"
            path.write_text('x = "C:" + "/service/data/orders.db"\n', encoding="utf-8")
            self.assertEqual([x.code for x in scan_file(path, Path(temp))], ["R23"])

    def test_tmp_path_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test_demo.py"
            path.write_text('x = tmp_path / "orders.db"\n', encoding="utf-8")
            self.assertEqual(scan_file(path, Path(temp)), [])

    def test_unreachable_assertion(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "test_demo.py"
            path.write_text("def test_x():\n    return\n    assert False\n", encoding="utf-8")
            self.assertIn("RD", [x.code for x in scan_file(path, Path(temp))])


if __name__ == "__main__":
    unittest.main()
