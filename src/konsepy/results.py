from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


@dataclass(frozen=True)
class ExtractionResult:
    """A labeled extraction result to simplify modular output writing."""
    label: Enum
    value: Any
    group: Optional[str] = None

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.value)



def get_result_label(result):
    if isinstance(result, ExtractionResult):
        return result.label
    return result
