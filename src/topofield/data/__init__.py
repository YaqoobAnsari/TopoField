"""Data generation and loading.

`synthetic` produces institutional-scale HDGs procedurally. These are for METHOD
DEVELOPMENT and PRETRAINING ONLY (plan §6.5) — they are never the real InstBuild
benchmark and are never used for evaluation claims. Every generated graph is
stamped as synthetic in its metadata.
"""

from .synthetic import generate_corpus, generate_hdg

__all__ = ["generate_hdg", "generate_corpus"]
