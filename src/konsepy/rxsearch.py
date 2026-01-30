from konsepy.context.contexts import get_contexts

_DEFAULT_WINDOW = 30


def search_first_regex(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    For each regex in the list, return only the first match found in the text.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator of results.
    """

    def _search_first_regex(text, *, include_match=False):
        found = False
        for regex, category, *other in regexes:
            funcs = _unpack_other_funcs(other)
            for m in regex.finditer(text):
                found = True
                yield from _yield_categories(m, category, funcs, text, window,
                                             word_window=word_window, include_match=include_match)
                break
            if found:
                break

    return _search_first_regex


def search_all_regex(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    For each regex in the list, return all matches found in the text.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator of results.
    """

    def _search_all_regex(text, *, include_match=False):
        for regex, category, *other in regexes:
            funcs = _unpack_other_funcs(other)
            for m in regex.finditer(text):
                yield from _yield_categories(m, category, funcs, text, window,
                                             word_window=word_window, include_match=include_match)

    return _search_all_regex


def get_all_regex_by_index(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    For each regex, return all results along with their start and end indices.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator of (result, match_text, start, end).
    """

    def _get_all_regex_by_index(text):
        for regex, category, *other in regexes:
            funcs = _unpack_other_funcs(other)
            for m in regex.finditer(text):
                for res in _yield_categories(m, category, funcs, text, window, word_window=word_window):
                    if isinstance(res, (list, tuple)):
                        res, m2 = res
                        yield res, m2.group(), m2.start(), m2.end()
                    else:
                        yield res, m.group(), m.start(), m.end()

    return _get_all_regex_by_index


def search_all_regex_match_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    For each regex, apply functions to the match object to determine the result.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator of results.
    """

    def _search_all_regex(text, *, include_match=False):
        for regex, category, *other in regexes:
            funcs = _unpack_other_funcs(other)
            for m in regex.finditer(text):
                yield from _yield_categories(m, category, funcs, text, window,
                                             word_window=word_window, include_match=include_match)

    return _search_all_regex


def _unpack_other_funcs(other):
    """
    Extract function(s) from optional arguments.

    Returns:
        List of functions or None.
    """
    if len(other) > 0:
        if isinstance(other[0], list):
            return other[0]
        else:
            return [other[0]]
    return None


def _yield_categories(m, category, funcs, text, window, *, word_window=None, include_match=False):
    """Helper to yield categories based on functions and match object."""
    if funcs:
        for func in funcs:
            if func and (res := func(**get_contexts(m, text, window, word_window=word_window))):
                if isinstance(res, list):
                    res, m = res  # category, match
                yield (res, m) if include_match else res
            else:
                yield (category, m) if include_match else category
    else:
        yield (category, m) if include_match else category


def search_and_replace_regex_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Search for regexes, but replace found text with dots to prevent double-matching.

    This is useful when one regex might be a subset of another or when you want to
    ensure each piece of text is only categorized once.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator of results.
    """

    def _search_all_regex(text, include_match=False):
        for regex, category, *other in regexes:
            funcs = _unpack_other_funcs(other)
            text_pieces = []
            prev_end = 0
            for m in regex.finditer(text):
                found = None
                if funcs:
                    for func in funcs:  # parse function in order
                        if res := func(**get_contexts(m, text, window, word_window=word_window)):
                            found = (res, m) if include_match else res
                            break
                if found:
                    if found is True or (include_match and found[0] is True):
                        continue  # no result
                    yield found
                else:
                    yield (category, m) if include_match else category
                text_pieces.append(text[prev_end:m.start()])
                text_pieces.append(f' {(len(m.group()) - 2) * "."} ')
                prev_end = m.end()
            text_pieces.append(text[prev_end:])
            text = ''.join(text_pieces)

    return _search_all_regex


def search_first_regex_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Return only the very first result found among all regexes.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator yielding at most one result.
    """

    def _search_first_regex(text, include_match=False):
        for regex, category, *other in regexes:
            funcs = _unpack_other_funcs(other)

            for m in regex.finditer(text):
                for res in _yield_categories(m, category, funcs, text, window,
                                             word_window=word_window, include_match=include_match):
                    yield res
                    return

    return _search_first_regex


def search_all_regex_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    For each regex, return all matches, running any provided context functions.

    Setting a regex to None acts as a sentinel value: if any non-UNKNOWN regex matched
    before the sentinel, processing stops.

    Args:
        regexes: List of tuples (regex, category, *other).
        window: Context window size for functions.
        word_window: Size of context window in terms of words (overrides default window)

    Returns:
        A function that takes text and returns a generator of results.
    """

    def _search_all_regex(text, include_match=False, ignore_indices=False):
        """
        ignore_indices: set to True for testing (so that the locating index doesn't need to be run)
        """
        found_non_unknown = False
        for regex, category, *other in regexes:
            if regex is None:
                if found_non_unknown:
                    # setting regex to None acts as sentinel value: continue only if only UNKNOWNs were found
                    break
                else:
                    continue

            funcs = _unpack_other_funcs(other)
            if len(other) > 1 and not ignore_indices:  # function to locate starting text
                indices = list(other[1](text))
            else:
                indices = [(0, len(text))]

            for start, end in indices:
                for m in regex.finditer(text, pos=start, endpos=end):
                    if funcs:
                        found_any = False
                        found = False
                        for func in funcs:
                            if func is None:
                                continue
                            if res := func(**get_contexts(m, text, window, word_window=word_window)):
                                yield (res, m) if include_match else res
                                found = True
                                found_any = True
                                if hasattr(res, 'name') and res.name != 'UNKNOWN':
                                    found_non_unknown = True
                                elif not hasattr(res, 'name') and res != 'UNKNOWN':
                                    found_non_unknown = True
                            if found:
                                break
                        if not found_any and category is not None:
                            yield (category, m) if include_match else category
                            if hasattr(category, 'name') and category.name != 'UNKNOWN':
                                found_non_unknown = True
                            elif not hasattr(category, 'name') and category != 'UNKNOWN':
                                found_non_unknown = True
                    elif category is not None:
                        yield (category, m) if include_match else category
                        if hasattr(category, 'name') and category.name != 'UNKNOWN':
                            found_non_unknown = True
                        elif not hasattr(category, 'name') and category != 'UNKNOWN':
                            found_non_unknown = True

    return _search_all_regex
