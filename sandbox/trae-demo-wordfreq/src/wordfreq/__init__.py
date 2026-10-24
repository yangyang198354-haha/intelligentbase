"""MOD-003 package — public API re-exports (implements IFC-010)."""
from .core import count_words, format_report, read_text, run, tokenize, top_words

__all__ = ["count_words", "format_report", "read_text", "run", "tokenize", "top_words"]
__version__ = "1.0.0"
