from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


@dataclass(frozen=True)
class ExtractionResult:
    """A labeled extraction result to simplify modular output writing."""
    label: Enum
    value: Any
    group: Optional[str] = None


def get_result_label(result):
    if isinstance(result, ExtractionResult):
        return result.label
    return result
