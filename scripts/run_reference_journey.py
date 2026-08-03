#!/usr/bin/env python3
"""Compatibility entry point for the deterministic reference journey."""

from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from product_os.reference_journey import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
