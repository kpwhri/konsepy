import re


def get_precontext(m, text, window=20, start=None, word_window=None, region_start=0):
    if start is None:
        start = m.start()
    if word_window:
        # for simplicity and correctness, we search backwards from start
        prefix = text[region_start:start]
        # find word boundaries
        words = re.findall(r'\w+', prefix)
        if len(words) > word_window:
            # find the start index of the nth word from the end
            matches = list(re.finditer(r'\w+', prefix))
            if len(matches) >= word_window:
                target_match = matches[-word_window]
                return prefix[target_match.start():]
        return prefix

    return text[max(region_start, start - window): start]


def get_postcontext(m, text, window=20, end=None, word_window=None, region_end=None):
    if end is None:
        end = m.end()
    if word_window:
        suffix = text[end:region_end]
        matches = list(re.finditer(r'\w+', suffix))
        if len(matches) >= word_window:
            target_match = matches[word_window - 1]
            return suffix[:target_match.end()]
        return suffix

    return text[end: min(region_end, end + window) if region_end else end + window]


def get_around(m, text, window=20, start=None, end=None, word_window=None, region=(0, None)):
    if start is None:
        start = m.start()
    if end is None:
        end = m.end()
    if word_window:
        pre = get_precontext(m, text, start=start, word_window=word_window, region_start=region[0])
        post = get_postcontext(m, text, end=end, word_window=word_window, region_end=region[1])
        return pre + text[start:end] + post

    return text[max(region[0], start - window): min(region[1], end + window) if region[1] else end + window]


def get_precontext_by_index(start, text, window=20, word_window=None, region_start=0):
    if word_window:
        # for simplicity and correctness, we search backwards from start
        prefix = text[region_start:start]
        # find word boundaries
        words = re.findall(r'\w+', prefix)
        if len(words) > word_window:
            # find the start index of the nth word from the end
            matches = list(re.finditer(r'\w+', prefix))
            if len(matches) >= word_window:
                target_match = matches[-word_window]
                return prefix[target_match.start():]
        return prefix

    return text[max(region_start, start - window): start]


def get_postcontext_by_index(end, text, window=20, word_window=None, region_end=None):
    if word_window:
        suffix = text[end:region_end]
        matches = list(re.finditer(r'\w+', suffix))
        if len(matches) >= word_window:
            target_match = matches[word_window - 1]
            return suffix[:target_match.end()]
        return suffix

    return text[end: min(region_end, end + window) if region_end else end + window]


def get_around_by_index(start, end, text, window=20,
                        word_window=None, region=(0, None)):
    if word_window:
        pre = get_precontext(start, text, start=start, word_window=word_window, region_start=region[0])
        post = get_postcontext(end, text, end=end, word_window=word_window, region_end=region[1])
        return pre + text[start:end] + post

    return text[max(region[0], start - window): min(region[1], end + window) if region[1] else end + window]


def get_contexts(m, text, window=20, context_match=None, context_window=None, context_direction=0,
                 word_window=None, region=(0, None)):
    """
    if matching on context of a previous match, the offsets will need to be updated. To do this, use:
        * context_match: previous match
        * context_window: previous window (supplied by `window` parameter)
        * context_direction: -1 for previous context, 1 for post-context

    `region`: allows limiting the contexts obtained to a particular region
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
        precontext = get_precontext(m, text, window, start=start, word_window=word_window, region_start=region[0])
        postcontext = get_postcontext(m, text, window, end=end, word_window=word_window, region_end=region[1])
        around = get_around(m, text, window, start=start, end=end, word_window=word_window, region=region)
    else:
        precontext = get_precontext(m, text, window, word_window=word_window, region_start=region[0])
        postcontext = get_postcontext(m, text, window, word_window=word_window, region_end=region[1])
        around = get_around(m, text, window, word_window=word_window, region=region)
    return {
        'm': m,
        'precontext': precontext,
        'postcontext': postcontext,
        'text': text,
        'window': window,
        'word_window': word_window,
        'around': around,
    }


def get_contexts_by_index(start, end, text, window=20, context_match=None, context_window=None, context_direction=0,
                          word_window=None, region=(0, None)):
    """
    if matching on context of a previous match, the offsets will need to be updated. To do this, use:
        * context_match: previous match
        * context_window: previous window (supplied by `window` parameter)
        * context_direction: -1 for previous context, 1 for post-context

    `region`: allows limiting the contexts obtained to a particular region
    """
    precontext = get_precontext_by_index(start, text, window, word_window=word_window, region_start=region[0])
    postcontext = get_postcontext_by_index(end, text, window, word_window=word_window, region_end=region[1])
    around = get_around_by_index(start, end, text, window, word_window=word_window, region=region)
    return {
        'precontext': precontext,
        'postcontext': postcontext,
        'text': text,
        'window': window,
        'word_window': word_window,
        'around': around,
    }


def check_if_pattern_after(pattern, m, text, window=20, banned_characters='.', end=None, return_concept=None, **kwargs):
    postcontext = get_postcontext(m, text, window=window, end=end)
    if m2 := pattern.search(postcontext):
        for ch in banned_characters:
            if ch in postcontext[:m2.start()]:
                return None
        return m2 if return_concept is None else return_concept


def check_if_pattern_before(pattern, m, text, window=20, banned_characters='.', start=None, return_concept=None,
                            **kwargs):
    precontext = get_precontext(m, text, window=window, start=start)
    if m2 := pattern.search(precontext):
        for ch in banned_characters:
            if ch in precontext[m2.end():]:
                return None
        return m2 if return_concept is None else return_concept


def check_if_pattern_around(pattern, m, text, window=20, banned_characters='.', start=None, end=None,
                            return_concept=None, **kwargs):
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
        return m2 if return_concept is None else return_concept
