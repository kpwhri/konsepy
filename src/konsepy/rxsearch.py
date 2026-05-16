from bisect import bisect_left
from warnings import warn

from konsepy.context.contexts import get_contexts

_DEFAULT_WINDOW = 30

SKIP = object()


def search_all_regex(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Search text with all regex definitions.

    REGEXES entries are expected to use the following structure:
        (regex, category, postprocessors, pre_processors)

    Positions:
        0. regex:
            A compiled regex pattern, or None as a sentinel.

        1. category:
            Default value yielded when the regex matches and no post-processor overrides or skips the result.

        2. postprocessors:
            Optional function or list/tuple of functions. Each function receives contextual keyword arguments from
            get_contexts(), including m, precontext, postcontext, text, window, word_window, and around.

            A post-processor may return:
                - None: no override; try the next processor, then category.
                - SKIP: skip this match entirely.
                - value: yield value instead of category.
                - (value, match): yield value and use match for include_match/index APIs.

        3. pre_processors:
            Optional function or list/tuple of functions. Each function receives text and should return or yield
            searchable (start, end) regions.

    Setting regex to None acts as a sentinel value:
        if any non-UNKNOWN value matched before the sentinel, processing stops.

    Args:
        regexes: Iterable of regex definition tuples.
        window: Context window size for post-processing functions.
        word_window: Size of context window in terms of words.

    Returns:
        A function that takes text and returns a generator of results.
    """
    return _search_regex(
        regexes,
        window=window,
        word_window=word_window,
        extractor=None,
    )


def search_first_regex(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Return only the first result found among all regexes.

    Args:
        regexes: Iterable of regex definition tuples.
        window: Context window size for post-processing functions.
        word_window: Size of context window in terms of words.

    Returns:
        A function that takes text and returns a generator yielding at most one result.
    """
    search_all = search_all_regex(regexes, window=window, word_window=word_window)

    def _search_first_regex(text, *, include_match=False, ignore_indices=False,
                            suppress_overlaps=False, categories_only=False):
        for result in search_all(
                text,
                include_match=include_match,
                ignore_indices=ignore_indices,
                suppress_overlaps=suppress_overlaps,
                categories_only=categories_only,
        ):
            yield result
            return

    return _search_first_regex


def extract_all_regex_target(
        regexes,
        window=_DEFAULT_WINDOW,
        word_window=None,
        *,
        target='target',
        transform=None,
        missing=SKIP,
        unmatched=SKIP,
):
    """
    Extract all values from a regex group, defaulting to the named group 'target'.

    Extraction happens before postprocessors. Postprocessors receive the extracted
    value as both 'extracted' and 'extracted_value'.

    Postprocessor behavior:
        - return SKIP to skip the match
        - return None to keep the extracted/default value
        - return any other value to override the extracted/default value
    """
    extractor = _make_extractor(
        target,
        transform=transform,
        missing=missing,
        unmatched=unmatched,
    )

    return _search_regex(
        regexes,
        window=window,
        word_window=word_window,
        extractor=extractor,
    )


def _search_regex(regexes, window=_DEFAULT_WINDOW, word_window=None, *, extractor=None):
    """
    Shared regex search engine.

    Args:
        regexes: Iterable of regex definition tuples.
        window: Context window size for postprocessors.
        word_window: Size of context window in terms of words.
        extractor: Optional callable used to extract a default result before
            postprocessors run.

    Returns:
        A function that takes text and returns a generator of results.
    """

    def _run_search(text, *, include_match=False, ignore_indices=False,
                    suppress_overlaps=False, categories_only=False):
        found_non_unknown = False
        claimed_spans = SpanTracker()

        for regex, category, *other in regexes:
            if regex is None:
                if found_non_unknown:
                    break
                continue

            postprocessors, preprocessors = _unpack_regex_args(other)

            if ignore_indices:
                regions = [(0, len(text))]
            else:
                regions = list(_get_search_regions(text, preprocessors))

            for start, end in regions:
                for m in regex.finditer(text, pos=start, endpos=end):
                    if suppress_overlaps and claimed_spans.overlaps(m.start(), m.end()):
                        continue

                    contexts = get_contexts(m, text, window, word_window=word_window)
                    default_result = category

                    if extractor is not None:
                        extracted = extractor(**contexts)

                        if extracted is SKIP:
                            continue

                        contexts['extracted'] = extracted
                        contexts['extracted_value'] = extracted

                        if extracted is not None:
                            default_result = extracted

                    result, result_match = _apply_postprocessors(
                        m,
                        default_result,
                        postprocessors,
                        contexts,
                    )

                    if result is None:
                        continue

                    if suppress_overlaps:
                        claimed_spans.add(m.start(), m.end())

                    yield (result, result_match) if include_match else result

                    if _is_non_unknown(result):
                        found_non_unknown = True

    return _run_search


def extract_first_regex_target(
        regexes,
        window=_DEFAULT_WINDOW,
        word_window=None,
        *,
        target='target',
        transform=None,
        missing=SKIP,
        unmatched=SKIP,
):
    """
    Extract the first value from a regex group, defaulting to the named group 'target'.

    Args:
        regexes: Iterable of regex definition tuples.
        window: Context window size for post-processing functions.
        word_window: Size of context window in terms of words.
        target: Group name or index to extract.
        transform: Optional callable used to transform the extracted value.
        missing: Value returned if the group does not exist. Defaults to SKIP.
        unmatched: Value returned if the group exists but did not match. Defaults to SKIP.

    Returns:
        A function that takes text and returns a generator yielding at most one extracted value.
    """
    search_all = extract_all_regex_target(
        regexes,
        window=window,
        word_window=word_window,
        target=target,
        transform=transform,
        missing=missing,
        unmatched=unmatched,
    )

    def _extract_first_regex(text, *, include_match=False, ignore_indices=False,
                             suppress_overlaps=False, categories_only=False):
        for result in search_all(
                text,
                include_match=include_match,
                ignore_indices=ignore_indices,
                suppress_overlaps=suppress_overlaps,
                categories_only=categories_only,
        ):
            yield result
            return

    return _extract_first_regex


def extract_group(name_or_index='target', *, missing=SKIP, unmatched=SKIP):
    """
    Return a post-processing function that extracts a regex group.

    Args:
        name_or_index: Group name or index to extract.
        missing: Value returned if the group does not exist. Defaults to SKIP.
        unmatched: Value returned if the group exists but did not match. Defaults to SKIP.

    Returns:
        A post-processing function.
    """

    def _extract_group(*, m, **_):
        try:
            value = m.group(name_or_index)
        except (IndexError, KeyError):
            return missing

        if value is None:
            return unmatched

        return value

    return _extract_group


def extract_group_as(name_or_index='target', transform=str, *, missing=SKIP, unmatched=SKIP):
    """
    Return a post-processing function that extracts and transforms a regex group.

    Args:
        name_or_index: Group name or index to extract.
        transform: Callable used to transform the extracted value.
        missing: Value returned if the group does not exist. Defaults to SKIP.
        unmatched: Value returned if the group exists but did not match. Defaults to SKIP.

    Returns:
        A post-processing function.
    """

    def _extract_group_as(*, m, **_):
        try:
            value = m.group(name_or_index)
        except (IndexError, KeyError):
            return missing

        if value is None:
            return unmatched

        return transform(value)

    return _extract_group_as


def get_all_regex_by_index(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Return all results along with their matched text and indices.

    Args:
        regexes: Iterable of regex definition tuples.
        window: Context window size for post-processing functions.
        word_window: Size of context window in terms of words.

    Returns:
        A function that takes text and returns a generator of (result, match_text, start, end).
    """
    search_all = search_all_regex(regexes, window=window, word_window=word_window)

    def _get_all_regex_by_index(text, *, ignore_indices=False,
                                suppress_overlaps=False, categories_only=False):
        for result, match in search_all(
                text,
                include_match=True,
                ignore_indices=ignore_indices,
                suppress_overlaps=suppress_overlaps,
                categories_only=categories_only,
        ):
            yield result, match.group(), match.start(), match.end()

    return _get_all_regex_by_index


def search_and_replace_regex_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Deprecated compatibility wrapper for overlap-suppressed search.

    This preserves the important behavior of the old search-and-replace function: earlier matches prevent later
    overlapping matches from being emitted. It no longer mutates the searched text.

    Args:
        regexes: Iterable of regex definition tuples.
        window: Context window size for post-processing functions.
        word_window: Size of context window in terms of words.

    Returns:
        A function that takes text and returns a generator of results.
    """
    warn(
        'search_and_replace_regex_func() is deprecated; use search_all_regex(...)(..., suppress_overlaps=True) instead.',
        DeprecationWarning,
        stacklevel=2,
    )

    search_all = search_all_regex(regexes, window=window, word_window=word_window)

    def _search_and_replace_regex(text, *, include_match=False,
                                  ignore_indices=False, categories_only=False):
        yield from search_all(
            text,
            include_match=include_match,
            ignore_indices=ignore_indices,
            suppress_overlaps=True,
            categories_only=categories_only,
        )

    return _search_and_replace_regex


def search_all_regex_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Deprecated alias for search_all_regex().
    """
    warn(
        'search_all_regex_func() is deprecated; use search_all_regex() instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    return search_all_regex(regexes, window=window, word_window=word_window)


def search_first_regex_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Deprecated alias for search_first_regex().
    """
    warn(
        'search_first_regex_func() is deprecated; use search_first_regex() instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    return search_first_regex(regexes, window=window, word_window=word_window)


def search_all_regex_match_func(regexes, window=_DEFAULT_WINDOW, word_window=None):
    """
    Deprecated alias for search_all_regex().
    """
    warn(
        'search_all_regex_match_func() is deprecated; use search_all_regex() instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    return search_all_regex(regexes, window=window, word_window=word_window)


class SpanTracker:
    """
    Track non-empty claimed spans and efficiently detect overlap.

    Spans are stored sorted by start. Adjacent spans do not overlap.
    """

    def __init__(self):
        self._spans = []

    def overlaps(self, start, end):
        """
        Return True if the candidate span overlaps any claimed span.
        """
        if start == end:
            return False

        index = bisect_left(self._spans, (start, end))

        if index > 0:
            previous_start, previous_end = self._spans[index - 1]
            if previous_start < end and start < previous_end:
                return True

        if index < len(self._spans):
            next_start, next_end = self._spans[index]
            if next_start < end and start < next_end:
                return True

        return False

    def add(self, start, end):
        """
        Add a span, merging any existing overlapping spans.
        """
        if start == end:
            return

        index = bisect_left(self._spans, (start, end))

        if index > 0 and self._spans[index - 1][1] >= start:
            index -= 1
            start = min(start, self._spans[index][0])
            end = max(end, self._spans[index][1])

        remove_until = index

        while remove_until < len(self._spans) and self._spans[remove_until][0] <= end:
            start = min(start, self._spans[remove_until][0])
            end = max(end, self._spans[remove_until][1])
            remove_until += 1

        self._spans[index:remove_until] = [(start, end)]


def _make_extractor(target, *, transform=None, missing=SKIP, unmatched=SKIP):
    if transform is None:
        return extract_group(target, missing=missing, unmatched=unmatched)

    return extract_group_as(
        target,
        transform,
        missing=missing,
        unmatched=unmatched,
    )


def _as_list(value):
    if value is None:
        return []

    if isinstance(value, (list, tuple)):
        return list(value)

    return [value]


def _unpack_regex_args(other):
    """
    Extract post-processing and pre-processing functions from optional arguments.
    """
    postprocessors = _as_list(other[0]) if len(other) > 0 else []
    preprocessors = _as_list(other[1]) if len(other) > 1 else []

    return postprocessors, preprocessors


def _get_search_regions(text, preprocessors):
    """
    Yield valid searchable regions from pre-processors.

    If no pre-processors are provided, the full text range is yielded.
    """
    if not preprocessors:
        yield 0, len(text)
        return

    for func in preprocessors:
        if func is None:
            continue

        regions = func(text)

        if regions is None:
            continue

        for region in regions:
            if region is None:
                continue

            start, end = region

            if start == end:
                continue

            yield start, end


def _apply_postprocessors(m, category, funcs, contexts):
    """
    Apply postprocessors to a match.

    Args:
        m: Regex match object.
        category: Default result if no postprocessor overrides.
        funcs: Postprocessor functions.
        contexts: Context dictionary passed to postprocessors.

    Returns:
        A tuple of (result, match). If the match should be skipped, returns
        (None, match).
    """
    for func in funcs:
        if func is None:
            continue

        res = func(**contexts)

        if res is SKIP:
            return None, m

        if res is not None:
            return _normalize_processor_result(res, m)

    if category is None:
        return None, m

    return category, m


def _normalize_processor_result(res, default_match):
    """
    Normalize a post-processor result to (result, match).
    """
    if isinstance(res, (list, tuple)) and len(res) == 2:
        return res

    return res, default_match


def _with_postprocessor(regexes, postprocessor):
    """
    Yield regex definitions with an additional post-processor prepended.
    """
    for regex, category, *other in regexes:
        existing_postprocessors = _as_list(other[0]) if len(other) > 0 else []
        preprocessors = other[1] if len(other) > 1 else None

        postprocessors = [postprocessor, *existing_postprocessors]

        if len(other) > 1:
            yield regex, category, postprocessors, preprocessors
        else:
            yield regex, category, postprocessors


def _is_non_unknown(value):
    if value is None:
        return False

    if hasattr(value, 'name'):
        return value.name != 'UNKNOWN'

    return value != 'UNKNOWN'
