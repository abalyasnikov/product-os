#!/usr/bin/env python3
"""Compatibility entry point for the Product OS installer."""

from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from product_decision_os.installer import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
