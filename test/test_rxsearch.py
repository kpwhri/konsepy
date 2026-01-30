import re
from enum import Enum
from konsepy.rxsearch import (
    search_first_regex,
    search_all_regex,
    get_all_regex_by_index,
    search_all_regex_match_func,
    search_and_replace_regex_func,
    search_first_regex_func,
    search_all_regex_func,
)


class KalevalaCategory(Enum):
    HERO = 1
    GOD = 2
    SMITH = 3
    UNKNOWN = 4


def test_search_first_regex():
    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.HERO),
        (re.compile(r'Ilmarinen', re.I), KalevalaCategory.SMITH),
    ]
    func = search_first_regex(regexes)

    text = 'Väinämöinen and Ilmarinen were friends.'
    results = list(func(text))
    assert results == [KalevalaCategory.HERO]

    text2 = 'Ilmarinen was a smith.'
    results2 = list(func(text2))
    assert results2 == [KalevalaCategory.SMITH]


def test_search_all_regex():
    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.HERO),
        (re.compile(r'Ilmarinen', re.I), KalevalaCategory.SMITH),
    ]
    func = search_all_regex(regexes)

    text = 'Väinämöinen and Ilmarinen were friends. Väinämöinen sang.'
    results = list(func(text))
    # search_all_regex iterates over regexes, then finditer for each
    # So it returns all matches for HERO first, then all for SMITH
    assert results == [KalevalaCategory.HERO, KalevalaCategory.HERO, KalevalaCategory.SMITH]


def test_get_all_regex_by_index():
    regexes = [
        (re.compile(r'Ukko', re.I), KalevalaCategory.GOD),
    ]
    func = get_all_regex_by_index(regexes)

    text = 'Ukko is the god of sky.'
    results = list(func(text))
    assert len(results) == 1
    assert results[0][0] == KalevalaCategory.GOD
    assert results[0][1] == 'Ukko'
    assert results[0][2] == 0
    assert results[0][3] == 4


def test_search_all_regex_match_func():
    def check_context(**kwargs):
        if 'old' in kwargs.get('text', '').lower():
            return KalevalaCategory.HERO
        return None

    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.UNKNOWN, check_context),
    ]
    func = search_all_regex_match_func(regexes)

    text = 'Old Väinämöinen sang.'
    results = list(func(text))
    assert results == [KalevalaCategory.HERO]

    text2 = 'Young Väinämöinen.'
    results2 = list(func(text2))
    # if func returns None, it falls back to category
    assert results2 == [KalevalaCategory.UNKNOWN]


def test_search_all_regex_match_func2():
    def check_context(precontext, **kwargs):
        if 'old' in precontext.lower():
            return KalevalaCategory.HERO
        return None

    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.UNKNOWN, check_context),
    ]
    func = search_all_regex_match_func(regexes)

    text = 'Old Väinämöinen sang.'
    results = list(func(text))
    assert results == [KalevalaCategory.HERO]

    text2 = 'Young Väinämöinen.'
    results2 = list(func(text2))
    # if func returns None, it falls back to category
    assert results2 == [KalevalaCategory.UNKNOWN]


def test_search_and_replace_regex_func():
    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.HERO),
        (re.compile(r'Väinä', re.I), KalevalaCategory.UNKNOWN),
    ]
    func = search_and_replace_regex_func(regexes)

    text = 'Väinämöinen'
    results = list(func(text))
    # first regex matches Väinämöinen, then it's replaced by dots, so 'Väinä' won't match anymore
    assert results == [KalevalaCategory.HERO]


def test_search_first_regex_func():
    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.HERO),
        (re.compile(r'Ilmarinen', re.I), KalevalaCategory.SMITH),
    ]
    func = search_first_regex_func(regexes)

    text = 'Väinämöinen and Ilmarinen.'
    results = list(func(text))
    assert results == [KalevalaCategory.HERO]


def test_search_all_regex_func_sentinel():
    regexes = [
        (re.compile(r'Väinämöinen', re.I), KalevalaCategory.HERO),
        (None, None),  # sentinel
        (re.compile(r'Ukko', re.I), KalevalaCategory.GOD),
    ]
    func = search_all_regex_func(regexes)

    text = 'Väinämöinen and Ukko.'
    results = list(func(text))
    # found HERO, so it stops at sentinel.
    assert results == [KalevalaCategory.HERO]

    text2 = 'Ukko alone.'
    results2 = list(func(text2))
    # HERO not found, so it continues past sentinel.
    assert results2 == [KalevalaCategory.GOD]


def test_search_all_regex_func_with_indices():
    def find_indices(text):
        yield 0, 10

    regexes = [
        (re.compile(r'Ukko', re.I), KalevalaCategory.GOD, [None], find_indices),
    ]
    func = search_all_regex_func(regexes)

    text = 'Ukko is here. Ukko is there.'
    results = list(func(text))
    # Only the first Ukko is in the first 10 chars.
    assert results == [KalevalaCategory.GOD]


def test_search_all_regex_func_word_window():
    def check_context(precontext, **kwargs):
        # With word_window=2, precontext for 'sang' should be 'Old Väinämöinen '
        if 'Old Väinämöinen' in precontext:
            return 'SINGER'

    regexes = [
        (re.compile(r'sang', re.I), 'UNKNOWN', check_context),
    ]
    # Use word_window=2
    func = search_all_regex_func(regexes, word_window=2)

    text = 'The wise Old Väinämöinen sang a song.'
    results = list(func(text))
    assert results == ['SINGER']

    # If word_window=1, precontext would be 'Väinämöinen '
    func2 = search_all_regex_func(regexes, word_window=1)
    results2 = list(func2(text))
    assert results2 == ['UNKNOWN']


def test_search_and_replace_regex_func_word_window():
    def check_context(postcontext, **kwargs):
        # with word_window=2, postcontext for 'Ilmarinen' should be ' forged the'
        if 'forged' in postcontext:
            return 'BLACKSMITH'

    regexes = [
        (re.compile(r'Ilmarinen', re.I), 'UNKNOWN', check_context),
    ]
    func = search_and_replace_regex_func(regexes, word_window=2)

    text = 'Ilmarinen forged the Sampo.'
    results = list(func(text))
    assert results == ['BLACKSMITH']


def test_search_first_regex_func_word_window():
    def check_context(around, **kwargs):
        # with word_window=1, around for 'Sampo' should be 'forged Sampo.'
        if 'forged' in around:
            return 'ARTEFACT'

    regexes = [
        (re.compile(r'Sampo', re.I), 'UNKNOWN', check_context),
    ]
    func = search_first_regex_func(regexes, word_window=1)

    text = 'Ilmarinen forged Sampo.'
    results = list(func(text))
    assert results == ['ARTEFACT']
