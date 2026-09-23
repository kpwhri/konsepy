import re


def get_last_match(pattern, text):
    last_match = None
    for match in re.finditer(pattern, text):
        last_match = match
    return last_match


def matches_pre(pat, text, banned_characters='.'):
    if m := get_last_match(pat, text):
        for ch in banned_characters:
            if ch in text[m.end():]:
                return None
        return m


def matches_post(pat, text, banned_characters='.'):
    if m := pat.search(text):
        for ch in banned_characters:
            if ch in text[:m.start()]:
                return None
        return m
