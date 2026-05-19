import re

import pytest

from konsepy.context.other_subject import has_other_subject, check_if_other_subject
from konsepy.rxsearch import SKIP


@pytest.mark.parametrize('pattern, text, banned_characters, exp', [
    ('drinks?', 'father drinks', '.', 'father'),
    ('drinks?', 'drinks mother', '.', None),
    ('drinks?', 'MOTHER drinks', '.', 'MOTHER'),
])
def test_other_subject_before(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    precontext = text[:m.start()]
    if res := has_other_subject(precontext, -1, banned_characters=banned_characters):
        assert res.group() == exp
    else:
        assert res == exp


@pytest.mark.parametrize('pattern, text, banned_characters, exp', [
    ('drinks?', 'father drinks', '.', None),
    ('drinks?', 'drinks mother', '.', 'mother'),
])
def test_other_subject_after(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    postcontext = text[m.end():]
    if res := has_other_subject(postcontext, 1, banned_characters=banned_characters):
        assert res.group() == exp
    else:
        assert res == exp


@pytest.mark.parametrize('pattern, text, banned_characters, exp', [
    ('drinks?', 'father drinks', '.', 'father'),
    ('drinks?', 'drinks mother', '.', 'mother'),
    ('drinks?', 'drinks at mother\'s home', '.', None),
    ('drinks?', 'according to father, drinks', '.', None),
])
def test_check_if_other_subject(pattern, text, banned_characters, exp):
    m = re.search(pattern, text, re.I)
    precontext = text[:m.start()]
    postcontext = text[m.end():]
    if res := check_if_other_subject(m, precontext, postcontext, text):
        if res is SKIP:  # other subjec was found
            m2 = check_if_other_subject(m, precontext, postcontext, text, return_match=True)
            assert m2.group() == exp
        else:
            assert res == exp  # just cause an error, this path should not be tread
    else:
        assert res == exp  # None
