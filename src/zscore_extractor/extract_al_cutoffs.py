#!/usr/bin/env python3
"""Compatibility wrapper for the modularized extractor."""

from pathlib import Path
import sys

try:
    from .cli import main
    from .parsing import extract_pdf
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from zscore_extractor.cli import main
    from zscore_extractor.parsing import extract_pdf

__all__ = ["main", "extract_pdf"]


if __name__ == "__main__":
    main()
