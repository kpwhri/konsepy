import re

import pytest

from konsepy.context.utils import matches_post, matches_pre


@pytest.mark.parametrize('text, pattern, expected_group, expected_span', [
    ('no chest pain', r'\bno\b', 'no', (0, 2)),
    ('patient denies fever', r'\bdenies\b', 'denies', (8, 14)),
])
def test_matches_post_returns_first_match_when_no_banned_character_before(
        text, pattern, expected_group, expected_span
):
    pat = re.compile(pattern)

    result = matches_post(pat, text)

    assert result is not None
    assert result.group() == expected_group
    assert result.span() == expected_span


def test_matches_post_returns_none_when_no_match():
    pat = re.compile(r'\bdenies\b')

    assert matches_post(pat, 'patient reports fever') is None


def test_matches_post_returns_none_when_default_banned_character_before_match():
    pat = re.compile(r'\bdenies\b')

    assert matches_post(pat, 'first sentence. patient denies fever') is None


def test_matches_post_allows_match_when_banned_characters_is_empty():
    pat = re.compile(r'\bdenies\b')

    result = matches_post(pat, 'first sentence. patient denies fever', banned_characters='')

    assert result is not None
    assert result.group() == 'denies'


def test_matches_post_respects_custom_banned_characters():
    pat = re.compile(r'\bdenies\b')

    assert matches_post(pat, 'family history; patient denies fever', banned_characters=';') is None

    result = matches_post(pat, 'family history. patient denies fever', banned_characters=';')

    assert result is not None
    assert result.group() == 'denies'


def test_matches_post_returns_none_when_newline_before_match_is_banned():
    pat = re.compile(r'\bdenies\b')

    assert matches_post(pat, 'family history\ndenies fever', banned_characters='.\n') is None


@pytest.mark.parametrize('text, pattern, expected_group, expected_span', [
    ('pain absent', r'\babsent\b', 'absent', (5, 11)),
    ('fever not present', r'\bnot\b', 'not', (6, 9)),
])
def test_matches_pre_returns_match_when_no_banned_character_after(
        text, pattern, expected_group, expected_span
):
    pat = re.compile(pattern)

    result = matches_pre(pat, text)

    assert result is not None
    assert result.group() == expected_group
    assert result.span() == expected_span


def test_matches_pre_returns_none_when_no_match():
    pat = re.compile(r'\babsent\b')

    assert matches_pre(pat, 'patient reports fever') is None


def test_matches_pre_returns_none_when_default_banned_character_after_match():
    pat = re.compile(r'\babsent\b')

    assert matches_pre(pat, 'fever absent. next sentence') is None


def test_matches_pre_allows_match_when_banned_characters_is_empty():
    pat = re.compile(r'\babsent\b')

    result = matches_pre(pat, 'fever absent. next sentence', banned_characters='')

    assert result is not None
    assert result.group() == 'absent'


def test_matches_pre_respects_custom_banned_characters():
    pat = re.compile(r'\babsent\b')

    assert matches_pre(pat, 'fever absent; next phrase', banned_characters=';') is None

    result = matches_pre(pat, 'fever absent. next sentence', banned_characters=';')

    assert result is not None
    assert result.group() == 'absent'


def test_matches_pre_returns_none_when_newline_after_match_is_banned():
    pat = re.compile(r'\babsent\b')

    assert matches_pre(pat, 'fever absent\nnext line', banned_characters='.\n') is None


def test_matches_pre_returns_last_match():
    pat = re.compile(r'\bno\b')

    result = matches_pre(pat, 'no fever and no cough')

    assert result is not None
    assert result.group() == 'no'
    assert result.span() == (13, 15)


def test_matches_pre_banned_character_check_is_after_last_match_only():
    pat = re.compile(r'\bno\b')

    result = matches_pre(pat, 'no fever. no cough')

    assert result is not None
    assert result.group() == 'no'
    assert result.span() == (10, 12)


def test_matches_post_banned_character_check_is_before_first_match_only():
    pat = re.compile(r'\bno\b')

    result = matches_post(pat, 'no fever. no cough')

    assert result is not None
    assert result.group() == 'no'
    assert result.span() == (0, 2)
