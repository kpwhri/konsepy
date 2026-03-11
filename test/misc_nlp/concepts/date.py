import enum
import re

from konsepy.rxsearch import search_and_replace_regex_func
from konsepy.rxutils import rx_compile


class DateMention(enum.Enum):
    YES = 1


MONTH = (
    r"January|February|March|April|May|June|July|August|September|"
    r"October|November|December"
)

REGEXES = [
    (
        rx_compile(
            rf"""
            \b(?:
                (?P<day>\d{{1,2}})(?:st|nd|rd|th)?
                \s+of\s+
                (?P<month>{MONTH})
                (?:,\s*(?P<year>\d{{4}}))?
                |
                (?P<month>{MONTH})
                \s+
                (?P<day>\d{{1,2}})(?:st|nd|rd|th)?
                (?:,\s*(?P<year>\d{{4}}))?
            )\b
            """,
            re.I | re.X,
        ),
        DateMention.YES,
    ),
]

RUN_REGEXES_FUNC = search_and_replace_regex_func(REGEXES)
