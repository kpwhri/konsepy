import re

from konsepy.context.contexts import get_contexts
from konsepy.context.utils import matches_pre, matches_post
from konsepy.rxsearch import SKIP

OTHER_SUBJECT = [
    'brother', 'sister', 'sibling', 'mother', 'mom', 'father', 'dad',
    'parent', 'dtr', 'daughter', 'son', 'child', 'children',
    'aunt', 'uncle', 'niece', 'nephew', 'cousin',
    'gma', 'grandma', 'grandmother', 'gpa', 'grandpa', 'grandfather',
    'grandparent', 'grandparents', r'grand\W*parent\(s\)',
    r'grand\W?daughter', 'gdtr',
    'husb(?:and)?', 'wife', 'wives', 'spouse', 'partner', r'(?:girl|boy)\W?friend',
    'neighbou?r', r'significant\W*other', 'person',
    'people', 'friend', 'kid', 'peer',
    'physician', 'doctor', 'family', r'co\W?worker',
    r'(?:house|room|flat)\W?mate', 'colleague', 'employe[re]', 'others',
    'family (?:history|hx)', 'maternal', 'paternal',
    'parents', r'parent\(s\)',
]

OTHER_SUBJECT_RX = re.compile('(?:{})'.format(
    '|'.join(rf'\b{x}\'?\b' for x in OTHER_SUBJECT)),
    re.I,
)


def has_other_subject(text, direction=0, other_subject_rx=OTHER_SUBJECT_RX, banned_characters='.'):
    """Return first mention of other subject

    direction = set to -1 (precontext) or 1 (postcontext) to ensure is in same sentence
    """
    if direction == -1:  # precontext
        return matches_pre(other_subject_rx, text, banned_characters)
    elif direction == 1:  # postcontext
        return matches_post(other_subject_rx, text, banned_characters)
    return None


# per/according to/at X's house
PER_PAT = re.compile(r'(?:\bper\b|according\W*to|\bat\b|\bdue\W*to\b|because\W*of\b)(?:\W+\w+)?\W*$', re.I)
OBJECT_PAT = re.compile(r'(?:\w+\W+)?(?:med\w*|gun|weapon|pill)s?', re.I)


def is_not_other_subject(m, precontext, postcontext, **kwargs):
    """Exceptions to other subject pattern"""
    if PER_PAT.search(precontext) or OBJECT_PAT.search(postcontext):
        return True
    return False


def check_if_other_subject(m, precontext, postcontext, text, window=30, banned_characters='.',
                           other_concept=SKIP, return_match=False, **kwargs):
    if m2 := has_other_subject(precontext, direction=-1, banned_characters=banned_characters):
        if is_not_other_subject(**get_contexts(
                m2, text, context_match=m, context_window=window, context_direction=-1,
        )):
            pass  # might still be in post-context
        else:
            return m2 if return_match else other_concept
    if m2 := has_other_subject(postcontext, direction=1, banned_characters=banned_characters):
        if is_not_other_subject(**get_contexts(
                m2, text, context_match=m, context_window=window, context_direction=1,
        )):
            pass
        else:
            return m2 if return_match else other_concept
    return None
