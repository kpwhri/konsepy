import re

import pytest

from konsepy.context.contexts import check_if_pattern_after


@pytest.mark.parametrize('pattern, pattern2, window, banned_characters, end, exp', [
    ('nose', 'help', 20, '.', None, None),
    ('nose', 'help', 20, '', None, 'help'),
])
def test_check_if_pattern_after(saiga_antelope, pattern, pattern2, window, banned_characters, end, exp):
    regex = re.compile(pattern2, re.I)
    if m := re.search(pattern, saiga_antelope, re.I):
        res = check_if_pattern_after(regex, m, saiga_antelope, window=window,
                                     banned_characters=banned_characters, end=end)
        if res:
            assert res.group() == exp
        else:
            assert res is None


@pytest.mark.parametrize('pattern, pattern2, window, banned_characters, end, exp', [
    ('help', 'nose', 20, '.', None, None),
    ('help', 'nose', 20, '', None, 'nose'),
])
def test_check_if_pattern_before(saiga_antelope, pattern, pattern2, window, banned_characters, end, exp):
    regex = re.compile(pattern2, re.I)
    if m := re.search(pattern, saiga_antelope, re.I):
        res = check_if_pattern_after(regex, m, saiga_antelope, window=window,
                                     banned_characters=banned_characters, end=end)
        if res:
            assert res.group() == exp
        else:
            assert res is None
