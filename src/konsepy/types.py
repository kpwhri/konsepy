"""
Types to simplify type hinting descriptions
"""
from enum import Enum
from typing import Pattern

RegexPattern = tuple[Pattern, Enum]
RegexList = list[RegexPattern]
RegexDict = dict[str, RegexList]
