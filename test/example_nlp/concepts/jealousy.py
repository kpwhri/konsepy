"""
Example concept.

"""
import enum
import re

from konsepy.context.negation import check_if_negated
from konsepy.context.other_subject import check_if_other_subject
from konsepy.regex import search_and_replace_regex_func


class Jealousy(enum.Enum):  # TODO: change 'Concept' to relevant concept name
    """Start from 1; each must be distinct; use CAPITAL_LETTERS_WITH_UNDERSCORE is possible"""
    NO = 0
    YES = 1
    FAMILY = 2


jealous = r'(?:jealous|env[yi])\w*'

REGEXES = [
    (
        re.compile(rf'\b{jealous}\b', re.I),
        Jealousy.YES,
        [
            lambda **kwargs: check_if_negated(neg_concept=Jealousy.NO, **kwargs),
            lambda **kwargs: check_if_other_subject(other_concept=Jealousy.FAMILY, **kwargs),
        ]
    ),
]

RUN_REGEXES_FUNC = search_and_replace_regex_func(REGEXES)  # find all occurrences of all regexes
