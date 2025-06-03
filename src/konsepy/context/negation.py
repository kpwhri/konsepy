import re

from konsepy.context.contexts import get_contexts

DEFAULT_PRENEG_PAT = re.compile(
    rf'\b(?:family|or|no concerns?|no|none|deny|denies|denied|(?:no|neg|negative)\W*to|not)\b'
)
DEFAULT_POSTNEG_PAT = re.compile(
    rf'\b(?:no concerns?|or|no|none|deny|denies|denied|absent|not at all)\b'
)


def is_not_negated(m, precontext, postcontext, banned_characters='.', **kwargs):
    return not (
            has_prenegation(precontext, banned_characters=banned_characters)
            or has_postnegation(postcontext, banned_characters=banned_characters)
    )


def check_if_negated(m, precontext, postcontext, text, window, neg_concept=True, **kwargs):
    direction = 0
    if m2 := has_negation(precontext, direction=-1, **kwargs):
        direction = -1
    elif m2 := has_negation(postcontext, direction=1, **kwargs):
        direction = 1
    if m2:
        if is_not_negated(**get_contexts(
                m2, text, context_match=m, context_window=window, context_direction=direction
        )):
            return None
        return neg_concept
    return None


def has_negation(text, direction=0, prenegation_pat=DEFAULT_PRENEG_PAT,
                 postnegation_pat=DEFAULT_POSTNEG_PAT, banned_characters='.',
                 m=None, window=20, **kwargs):
    """Return first mention of negation, looking both backward or forward through the text.

    direction = set to -1 (precontext) or 1 (postcontext) to ensure is in same sentence
    """
    if m is not None:
        pretext = text[max(0, m.start() - window):m.start()]
        posttext = text[m.end(): m.end() + window]
    else:
        pretext = text
        posttext = text
    if direction == -1:  # precontext
        return has_prenegation(pretext, prenegation_pat, banned_characters)
    elif direction == 1:  # postcontext
        return has_postnegation(posttext, postnegation_pat, banned_characters)
    elif direction == 0:  # both directions
        return (has_prenegation(pretext, prenegation_pat, banned_characters)
                or has_postnegation(posttext, postnegation_pat, banned_characters))
    else:
        raise ValueError(f'Unexpected negation direction: {direction} (expected: -1 [pre], 0 [both], or 1 [post]).')


def has_prenegation(text, prenegation_pat=DEFAULT_PRENEG_PAT, banned_characters='.'):
    if m := prenegation_pat.search(text):
        for ch in banned_characters:
            if ch in text[m.end():]:
                return None
        return m


def has_postnegation(text, postnegation_pat=DEFAULT_POSTNEG_PAT, banned_characters='.'):
    if m := postnegation_pat.search(text):
        for ch in banned_characters:
            if ch in text[:m.start()]:
                return None
        return m
