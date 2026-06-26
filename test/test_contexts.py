import re

import pytest

from konsepy.context.contexts import check_if_pattern_after, get_contexts


@pytest.mark.parametrize('pattern, word_window, exp_pre, exp_post, exp_around', [
    ('Väinämöinen', 2, 'The old ', ' played the', 'The old Väinämöinen played the'),
    ('kantele', 3, 'Väinämöinen played the ', '.', 'Väinämöinen played the kantele.'),
    ('The', 2, '', ' old Väinämöinen', 'The old Väinämöinen'),
    ('played', 10, 'The old Väinämöinen ', ' the kantele.', 'The old Väinämöinen played the kantele.'),
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


@pytest.mark.parametrize('pattern, region_text, window, exp_pre, exp_post, exp_around', [
    (
            'Ilmarinen',
            'Ilmarinen forged the Sampo',
            50,
            '',
            ' forged the Sampo',
            'Ilmarinen forged the Sampo',
    ),
    (
            'forged',
            'Ilmarinen forged the Sampo',
            50,
            'Ilmarinen ',
            ' the Sampo',
            'Ilmarinen forged the Sampo',
    ),
    (
            'Sampo',
            'Ilmarinen forged the Sampo',
            50,
            'Ilmarinen forged the ',
            '',
            'Ilmarinen forged the Sampo',
    ),
])
def test_get_contexts_respects_region_boundaries(pattern, region_text, window, exp_pre, exp_post, exp_around):
    text = f'Louhi watched. {region_text}. Väinämöinen sang.'
    region_start = text.index(region_text)
    region_end = region_start + len(region_text)

    m = re.search(pattern, text)
    res = get_contexts(m, text, window=window, region=(region_start, region_end))

    assert res['precontext'] == exp_pre
    assert res['postcontext'] == exp_post
    assert res['around'] == exp_around


@pytest.mark.parametrize('pattern, word_window, exp_pre, exp_post, exp_around', [
    (
            'Ilmarinen',
            2,
            '',
            ' forged the',
            'Ilmarinen forged the',
    ),
    (
            'forged',
            2,
            'Ilmarinen ',
            ' the Sampo',
            'Ilmarinen forged the Sampo',
    ),
    (
            'Sampo',
            2,
            'forged the ',
            '',
            'forged the Sampo',
    ),
])
def test_get_contexts_word_window_respects_region_boundaries(pattern, word_window, exp_pre, exp_post, exp_around):
    region_text = 'Ilmarinen forged the Sampo'
    text = f'Louhi watched. {region_text}. Väinämöinen sang.'
    region_start = text.index(region_text)
    region_end = region_start + len(region_text)

    m = re.search(pattern, text)
    res = get_contexts(m, text, word_window=word_window, region=(region_start, region_end))

    assert res['precontext'] == exp_pre
    assert res['postcontext'] == exp_post
    assert res['around'] == exp_around


def test_get_contexts_context_match_respects_region_boundaries_for_previous_context():
    text = 'Louhi watched. old Ilmarinen forged the Sampo. Väinämöinen sang.'
    region_start = text.index('old Ilmarinen')
    region_end = text.index('. Väinämöinen')

    context_match = re.search('Ilmarinen', text)
    precontext = text[max(0, context_match.start() - 20):context_match.start()]
    m = re.search('old', precontext)

    res = get_contexts(
        m,
        text,
        window=50,
        context_match=context_match,
        context_window=20,
        context_direction=-1,
        region=(region_start, region_end),
    )

    assert res['precontext'] == ''
    assert res['postcontext'] == ' Ilmarinen forged the Sampo'
    assert res['around'] == 'old Ilmarinen forged the Sampo'


def test_get_contexts_context_match_respects_region_boundaries_for_post_context():
    text = 'Louhi watched. Ilmarinen forged the Sampo with skill. Väinämöinen sang.'
    region_start = text.index('Ilmarinen')
    region_end = text.index('. Väinämöinen')

    context_match = re.search('Ilmarinen', text)
    postcontext = text[context_match.end():context_match.end() + 50]
    m = re.search('Sampo', postcontext)

    res = get_contexts(
        m,
        text,
        window=50,
        context_match=context_match,
        context_window=50,
        context_direction=1,
        region=(region_start, region_end),
    )

    assert res['precontext'] == 'Ilmarinen forged the '
    assert res['postcontext'] == ' with skill'
    assert res['around'] == 'Ilmarinen forged the Sampo with skill'
