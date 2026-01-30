def get_precontext(m, text, window=20, start=None):
    """
    TODO: add word window
    """
    if start is None:
        start = m.start()
    return text[max(0, start - window): start]


def get_postcontext(m, text, window=20, end=None):
    if end is None:
        end = m.end()
    return text[end: end + window]


def get_around(m, text, window=20, start=None, end=None):
    if start is None:
        start = m.start()
    if end is None:
        end = m.end()
    return text[max(0, start - window): end + window]


def get_contexts(m, text, window=20, context_match=None, context_window=None, context_direction=0):
    """
    if matching on context of a previous match, the offsets will need to be updated. To do this, use:
        * context_match: previous match
        * context_window: previous window (supplied by `window` parameter)
        * context_direction: -1 for previous context, 1 for post-context
    """
    if context_match:
        if context_direction == -1:
            offset = max(0, context_match.start() - context_window)
            start = offset + m.start()
            end = offset + m.end()
        elif context_direction == 1:
            offset = context_match.end()
            start = offset + m.start()
            end = offset + m.end()
        else:
            raise ValueError(fr'Unrecognized context direction: {context_direction};'
                             ' expected -1 [before] or +1 [after]')
        precontext = get_precontext(m, text, window, start=start)
        postcontext = get_postcontext(m, text, window, end=end)
        around = get_around(m, text, window, start=start, end=end)
    else:
        precontext = get_precontext(m, text, window)
        postcontext = get_postcontext(m, text, window)
        around = get_around(m, text, window)
    return {
        'm': m,
        'precontext': precontext,
        'postcontext': postcontext,
        'text': text,
        'window': window,
        'around': around,
    }


def check_if_pattern_after(pattern, m, text, window=20, banned_characters='.', end=None, return_concept=None, **kwargs):
    postcontext = get_postcontext(m, text, window=window, end=end)
    if m2 := pattern.search(postcontext):
        for ch in banned_characters:
            if ch in postcontext[:m2.start()]:
                return None
        yield m2 if return_concept is None else return_concept


def check_if_pattern_before(pattern, m, text, window=20, banned_characters='.', start=None, return_concept=None, **kwargs):
    precontext = get_precontext(m, text, window=window, start=start)
    if m2 := pattern.search(precontext):
        for ch in banned_characters:
            if ch in precontext[m2.end():]:
                return None
        yield m2 if return_concept is None else return_concept


def check_if_pattern_around(pattern, m, text, window=20, banned_characters='.', start=None, end=None, return_concept=None, **kwargs):
    around = get_around(m, text, window, start=start, end=end)
    for m2 in pattern.finditer(around):
        if m2.end() < m.start():  # match before
            for ch in banned_characters:
                if ch in around[m2.end():m.start()]:
                    continue
        elif m2.start() > m.end():
            for ch in banned_characters:
                if ch in around[m.end():m2.start()]:
                    continue
        yield m2 if return_concept is None else return_concept
