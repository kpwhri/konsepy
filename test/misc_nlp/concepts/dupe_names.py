import enum
import re
from konsepy.rxutils import rx_compile
from konsepy.rxsearch import search_all_regex_func


class Dupe(enum.Enum):
    NO = 0
    YES = 1


pattern = r'(?:score: (?P<val>\d+)|results: (?P<val>\d+))'
REGEXES = [
    (
        rx_compile(pattern, re.I),
        Dupe.YES,
        []
    ),
]

RUN_REGEXES_FUNC = search_all_regex_func(REGEXES)
