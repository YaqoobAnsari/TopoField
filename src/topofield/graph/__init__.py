"""HDG construction, validation, and statistics.

The HDG is the project's contract (docs/research_plan_final.md §4.3). Everything
downstream — extraction, simulation labels, models, metrics — composes against
this package and the schema it enforces.
"""

from .hdg import DELTA, HDG, LEVELS, TAU, load_hdg
from .validate import ValidationResult, validate, validate_file

__all__ = [
    "HDG",
    "LEVELS",
    "TAU",
    "DELTA",
    "load_hdg",
    "validate",
    "validate_file",
    "ValidationResult",
]
