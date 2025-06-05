"""
Example concept.

"""
import enum
import re

from konsepy.context.negation import check_if_negated
from konsepy.context.other_subject import check_if_other_subject
from konsepy.regex import search_and_replace_regex_func


class Justice(enum.Enum):  # TODO: change 'Concept' to relevant concept name
    """Start from 1; each must be distinct; use CAPITAL_LETTERS_WITH_UNDERSCORE is possible"""
    NO = 0
    YES = 1


justice = r'(?:just|legitima|fair|due\W*process|right[fe])\w*'

REGEXES = [
    (
        re.compile(rf'\b{justice}\b', re.I),
        Justice.YES,
        [
            lambda **kwargs: check_if_negated(neg_concept=Justice.NO, **kwargs),
        ]
    ),
]

RUN_REGEXES_FUNC = search_and_replace_regex_func(REGEXES)  # find all occurrences of all regexes
