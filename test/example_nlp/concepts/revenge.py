"""
Example concept.

"""
import enum
import re

from konsepy.context.negation import check_if_negated
from konsepy.context.other_subject import check_if_other_subject
from konsepy.regex import search_and_replace_regex_func


class Revenge(enum.Enum):
    NO = 0
    YES = 1


revenge = r'(?:revenge|venge|retribut|repris|aveng[ei]|retaliat|satisfact)\w*'

REGEXES = [
    (
        re.compile(rf'\b{revenge}\b', re.I),
        Revenge.YES,
        [
            lambda **kwargs: check_if_negated(neg_concept=Revenge.NO, **kwargs),
        ]
    ),
]

RUN_REGEXES_FUNC = search_and_replace_regex_func(REGEXES)  # find all occurrences of all regexes
