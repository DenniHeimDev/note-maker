"""Test configuration.

GitHub Actions appears to run Python with a safe import path where the working
directory isn't automatically importable. Ensure the repo root is on sys.path so
`import note_maker` works without installing the package.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
