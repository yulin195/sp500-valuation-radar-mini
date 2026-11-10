import io
import unittest
from contextlib import redirect_stdout

from radar_mini import __version__
from radar_mini.cli import main


class CliSmokeTest(unittest.TestCase):
    def test_noop_prints_version_and_usage(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main([])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn(__version__, out)
        self.assertIn("usage:", out)


if __name__ == "__main__":
    unittest.main()
