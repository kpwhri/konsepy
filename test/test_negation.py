import re

import pytest

from konsepy.context.negation import has_prenegation, has_postnegation, has_negation, is_not_negated

_preneg = [
    # (pattern, text, banned, exp_pre, exp_any)
    ('cancer', 'no cancer', '.', 'no', 'no'),
    ('cancer', 'cancer: no', '.', None, 'no'),
    ('cancer', 'smoking: no. Cancer diagnosis', '.', None, None),  # intervening banned char
    ('cancer', 'smoking: no. Cancer diagnosis', '', 'no', 'no'),  # remove banned char
]

_postneg = [
    # (pattern, text, banned, exp_post, exp_any)
    ('cancer', 'no cancer', '.', None, 'no'),
    ('cancer', 'cancer absent', '.', 'absent', 'absent'),
    ('cancer', 'cancer: no', ':', None, None),  # intervening banned char
    ('cancer', 'cancer: no', '.', 'no', 'no'),  # remove banned char
]

preneg = [x[0:4] for x in _preneg]  # remove exp_any
postneg = [x[0:4] for x in _postneg]  # remove exp_any
# looks for both, but from either pre-context or post context of match
allneg = [x[0:3] + (x[4],) for x in _preneg + _postneg]
# looks from left end or right end of the text (regardless of the match)
anyneg = [x[:3] for x in _preneg + _postneg]


@pytest.mark.parametrize('pattern, text, banned_characters, exp', preneg)
def test_has_prenegation(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    if res := has_prenegation(text[:m.start()], banned_characters=banned_characters):
        assert res.group() == exp
    else:
        assert res is None


@pytest.mark.parametrize('pattern, text, banned_characters, exp', preneg)
def test_has_negation_neg1_direction(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    if res := has_negation(text[:m.start()], direction=-1, banned_characters=banned_characters):
        assert res.group() == exp
    else:
        assert res is None


@pytest.mark.parametrize('pattern, text, banned_characters, exp', postneg)
def test_has_postnegation(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    if res := has_postnegation(text[m.end():], banned_characters=banned_characters):
        assert res.group() == exp
    else:
        assert res is None


@pytest.mark.parametrize('pattern, text, banned_characters, exp', postneg)
def test_has_postnegation(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    if res := has_negation(text[m.end():], direction=1, banned_characters=banned_characters):
        assert res.group() == exp
    else:
        assert res is None


@pytest.mark.parametrize('pattern, text, banned_characters, exp', allneg)
def test_has_negation(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    if res := has_negation(text, direction=0, banned_characters=banned_characters, m=m):
        assert res.group() == exp
    else:
        assert res is None


@pytest.mark.parametrize('pattern, text, banned_characters, exp', allneg)
def test_not_negated(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    res = is_not_negated(m, text[:m.start()], text[m.end():], banned_characters=banned_characters)
    assert res is not bool(exp)


@pytest.mark.parametrize('pattern, text, banned_characters', anyneg)
def test_any_negation(pattern, text, banned_characters):
    m = re.search(pattern, text, re.I)
    res = has_negation(text, direction=0, banned_characters=banned_characters)
    assert res is not None
