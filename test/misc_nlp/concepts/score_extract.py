import enum
import re

from konsepy.results import ExtractionResult
from konsepy.rxsearch import extract_all_regex_target


class ScoreCategory(enum.Enum):
    SCORE = 1
    UNKNOWN = -1


def label_score(*, extracted, m, **_):
    group = None
    if m.groupdict():
        group = m.groupdict().get('group')
    if group is not None:
        group = group.lower()
    return ExtractionResult(
        label=ScoreCategory.SCORE,
        value=extracted,
        group=group,
    )


REGEXES = [
    (
        re.compile(r'(?P<group>mobility|pain)\s+score\s*:\s*(?P<target>\d+)', re.I),
        None,
        label_score,
    ),
    (
        re.compile(r'\bscore\s*:\s*(?P<target>\d+)\b', re.I),
        None,
        label_score,
    ),
]

RUN_REGEXES_FUNC = extract_all_regex_target(REGEXES, transform=int)
