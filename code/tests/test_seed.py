import os
import unittest
from unittest.mock import patch

from shared_util.seed import seed_everything


class SeedTests(unittest.TestCase):
    def test_uses_large_deterministic_cublas_workspace(self):
        with patch.dict(os.environ, {}, clear=False):
            seed_everything(405)

            self.assertEqual(os.environ["CUBLAS_WORKSPACE_CONFIG"], ":4096:8")


if __name__ == "__main__":
    unittest.main()
