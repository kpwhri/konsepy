import re

import pytest

from konsepy.context.contexts import check_if_pattern_after, get_contexts


@pytest.mark.parametrize('pattern, word_window, exp_pre, exp_post, exp_around', [
    ('Väinämöinen', 2, 'The old ', ' played the', 'The old Väinämöinen played the'),
    ('kantele', 3, 'Väinämöinen played the ', '.', 'Väinämöinen played the kantele.'),
])
def test_get_contexts_word_window(pattern, word_window, exp_pre, exp_post, exp_around):
    text = 'The old Väinämöinen played the kantele.'
    m = re.search(pattern, text)
    res = get_contexts(m, text, word_window=word_window)
    assert res['precontext'] == exp_pre
    assert res['postcontext'] == exp_post
    assert res['around'] == exp_around


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
