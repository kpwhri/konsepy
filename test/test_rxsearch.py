import re
from enum import Enum

import pytest

from konsepy.rxsearch import (
    SKIP,
    SpanTracker,
    extract_all_regex_target,
    extract_first_regex_target,
    extract_group,
    extract_group_as,
    get_all_regex_by_index,
    search_all_regex,
    search_first_regex,
    # deprecated funcs (to be removed in future)
    search_all_regex_func,
    search_all_regex_match_func,
    search_and_replace_regex_func,
    search_first_regex_func,
)


class Category(Enum):
    UNKNOWN = 'UNKNOWN'
    HERO = 'HERO'
    NEGATED_HERO = 'NEGATED_HERO'
    PLACE = 'PLACE'
    NUMBER = 'NUMBER'


def test_search_all_regex_returns_all_default_categories():
    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO),
        (re.compile(r'Kalevala'), Category.PLACE),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen sang in Kalevala.')) == [
        Category.HERO,
        Category.PLACE,
    ]


def test_search_all_regex_returns_repeated_matches_for_same_regex():
    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen met Väinämöinen.')) == [
        Category.HERO,
        Category.HERO,
    ]


def test_search_first_regex_returns_only_first_result():
    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO),
        (re.compile(r'Kalevala'), Category.PLACE),
    ]

    search = search_first_regex(regexes)

    assert list(search('Väinämöinen sang in Kalevala.')) == [Category.HERO]


def test_search_first_regex_returns_empty_list_when_no_match():
    regexes = [
        (re.compile(r'Ilmarinen'), Category.HERO),
    ]

    search = search_first_regex(regexes)

    assert list(search('Väinämöinen sang.')) == []


def test_include_match_returns_result_and_match_object():
    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO),
    ]

    search = search_all_regex(regexes)
    results = list(search('old Väinämöinen sang', include_match=True))

    assert len(results) == 1

    result, match = results[0]

    assert result == Category.HERO
    assert match.group() == 'Väinämöinen'
    assert match.start() == 4
    assert match.end() == 15


def test_get_all_regex_by_index_returns_match_text_and_indices():
    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO),
        (re.compile(r'Kalevala'), Category.PLACE),
    ]

    get_by_index = get_all_regex_by_index(regexes)

    assert list(get_by_index('Väinämöinen in Kalevala')) == [
        (Category.HERO, 'Väinämöinen', 0, 11),
        (Category.PLACE, 'Kalevala', 15, 23),
    ]


def test_postprocessor_can_override_category():
    def classify_hero(**_):
        return Category.HERO

    regexes = [
        (re.compile(r'singer'), Category.UNKNOWN, classify_hero),
    ]

    search = search_all_regex(regexes)

    assert list(search('the singer arrived')) == [Category.HERO]


def test_postprocessor_none_falls_back_to_category_once():
    calls = []

    def no_override(**_):
        calls.append('called')
        return None

    regexes = [
        (re.compile(r'kantele'), Category.HERO, [no_override, no_override]),
    ]

    search = search_all_regex(regexes)

    assert list(search('kantele')) == [Category.HERO]
    assert calls == ['called', 'called']


def test_postprocessor_skip_suppresses_match():
    def skip_match(**_):
        return SKIP

    regexes = [
        (re.compile(r'Louhi'), Category.HERO, skip_match),
    ]

    search = search_all_regex(regexes)

    assert list(search('Louhi')) == []


def test_postprocessor_falsey_values_are_valid_overrides():
    def zero(**_):
        return 0

    regexes = [
        (re.compile(r'zero'), Category.UNKNOWN, zero),
    ]

    search = search_all_regex(regexes)

    assert list(search('zero')) == [0]


def test_postprocessor_tuple_result_replaces_match_for_include_match():
    regex = re.compile(r'(?P<prefix>old)\s+(?P<target>Väinämöinen)')

    def target_match(*, m, **_):
        return Category.HERO, m

    regexes = [
        (regex, Category.UNKNOWN, target_match),
    ]

    search = search_all_regex(regexes)
    results = list(search('old Väinämöinen', include_match=True))

    assert len(results) == 1
    assert results[0][0] == Category.HERO
    assert results[0][1].group() == 'old Väinämöinen'


def test_postprocessor_list_and_tuple_are_both_supported():
    def no_override(**_):
        return None

    def classify(**_):
        return Category.HERO

    list_regexes = [
        (re.compile(r'Aino'), Category.UNKNOWN, [no_override, classify]),
    ]
    tuple_regexes = [
        (re.compile(r'Aino'), Category.UNKNOWN, (no_override, classify)),
    ]

    assert list(search_all_regex(list_regexes)('Aino')) == [Category.HERO]
    assert list(search_all_regex(tuple_regexes)('Aino')) == [Category.HERO]


def test_postprocessor_receives_context_arguments():
    seen = {}

    def inspect_context(**context):
        seen.update(context)
        return Category.HERO

    regexes = [
        (re.compile(r'Väinämöinen'), Category.UNKNOWN, inspect_context),
    ]

    search = search_all_regex(regexes, window=4, word_window=2)

    assert list(search('old Väinämöinen sang')) == [Category.HERO]
    assert seen['m'].group() == 'Väinämöinen'
    assert seen['text'] == 'old Väinämöinen sang'
    assert seen['window'] == 4
    assert seen['word_window'] == 2
    assert 'precontext' in seen
    assert 'postcontext' in seen
    assert 'around' in seen


def test_category_none_skips_match_when_no_processor_result():
    regexes = [
        (re.compile(r'Väinämöinen'), None),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen')) == []


def test_preprocessor_limits_search_region():
    text = 'Väinämöinen first. Väinämöinen second.'

    def first_sentence(text):
        yield 0, text.index('.')

    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO, None, first_sentence),
    ]

    search = search_all_regex(regexes)

    assert list(search(text)) == [Category.HERO]


def test_preprocessor_list_and_tuple_are_both_supported():
    text = 'Aino then Ilmarinen then Louhi'

    def aino_region(text):
        yield text.index('Aino'), text.index('Aino') + len('Aino')

    def louhi_region(text):
        yield text.index('Louhi'), text.index('Louhi') + len('Louhi')

    list_regexes = [
        (re.compile(r'Aino|Louhi'), Category.HERO, None, [aino_region, louhi_region]),
    ]
    tuple_regexes = [
        (re.compile(r'Aino|Louhi'), Category.HERO, None, (aino_region, louhi_region)),
    ]

    assert list(search_all_regex(list_regexes)(text)) == [Category.HERO, Category.HERO]
    assert list(search_all_regex(tuple_regexes)(text)) == [Category.HERO, Category.HERO]


def test_preprocessor_none_and_empty_regions_are_ignored():
    text = 'Väinämöinen and Ilmarinen'

    def regions(text):
        yield None
        yield 0, 0
        yield text.index('Ilmarinen'), text.index('Ilmarinen') + len('Ilmarinen')

    regexes = [
        (re.compile(r'Väinämöinen|Ilmarinen'), Category.HERO, None, regions),
    ]

    search = search_all_regex(regexes)

    assert list(search(text)) == [Category.HERO]


def test_preprocessor_returning_none_yields_no_regions():
    def no_regions(text):
        return None

    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO, None, no_regions),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen')) == []


def test_ignore_indices_searches_full_text_despite_preprocessor():
    def no_regions(text):
        return None

    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO, None, no_regions),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen')) == []
    assert list(search('Väinämöinen', ignore_indices=True)) == [Category.HERO]


def test_sentinel_stops_after_non_unknown_enum_result():
    regexes = [
        (re.compile(r'Väinämöinen'), Category.HERO),
        (None, None),
        (re.compile(r'Louhi'), Category.UNKNOWN),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen Louhi')) == [Category.HERO]


def test_sentinel_allows_unknown_fallback_when_only_unknown_found_before_sentinel():
    regexes = [
        (re.compile(r'unknown'), Category.UNKNOWN),
        (None, None),
        (re.compile(r'Louhi'), Category.HERO),
    ]

    search = search_all_regex(regexes)

    assert list(search('unknown Louhi')) == [Category.UNKNOWN, Category.HERO]


def test_sentinel_stops_after_non_unknown_string_result():
    regexes = [
        (re.compile(r'Väinämöinen'), 'HERO'),
        (None, None),
        (re.compile(r'Louhi'), 'UNKNOWN'),
    ]

    search = search_all_regex(regexes)

    assert list(search('Väinämöinen Louhi')) == ['HERO']


def test_extract_group_defaults_to_target_group():
    regexes = [
        (re.compile(r'hero:\s*(?P<target>\w+)'), Category.HERO, extract_group()),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero: Aino')) == ['Aino']


def test_extract_group_supports_custom_group_name():
    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.HERO, extract_group('name')),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero: Aino')) == ['Aino']


def test_extract_group_supports_group_index():
    regexes = [
        (re.compile(r'hero:\s*(\w+)'), Category.HERO, extract_group(1)),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero: Aino')) == ['Aino']


def test_extract_group_missing_defaults_to_skip():
    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.HERO, extract_group()),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero: Aino')) == []


def test_extract_group_missing_can_fall_back_to_category():
    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.HERO, extract_group(missing=None)),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero: Aino')) == [Category.HERO]


def test_extract_group_unmatched_defaults_to_skip():
    regexes = [
        (re.compile(r'hero(?::\s*(?P<target>\w+))?'), Category.HERO, extract_group()),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero')) == []


def test_extract_group_unmatched_can_fall_back_to_category():
    regexes = [
        (re.compile(r'hero(?::\s*(?P<target>\w+))?'), Category.HERO, extract_group(unmatched=None)),
    ]

    search = search_all_regex(regexes)

    assert list(search('hero')) == [Category.HERO]


def test_extract_group_as_transforms_value():
    regexes = [
        (re.compile(r'number:\s*(?P<target>\d+)'), Category.NUMBER, extract_group_as(transform=int)),
    ]

    search = search_all_regex(regexes)

    assert list(search('number: 12')) == [12]


def test_extract_group_as_preserves_falsey_transformed_value():
    regexes = [
        (re.compile(r'number:\s*(?P<target>\d+)'), Category.NUMBER, extract_group_as(transform=int)),
    ]

    search = search_all_regex(regexes)

    assert list(search('number: 0')) == [0]


def test_extract_all_regex_target_extracts_all_targets():
    regexes = [
        (re.compile(r'hero:\s*(?P<target>\w+)'), Category.HERO),
    ]

    extract = extract_all_regex_target(regexes)

    assert list(extract('hero: Aino hero: Louhi')) == ['Aino', 'Louhi']


def test_extract_first_regex_target_extracts_only_first_target():
    regexes = [
        (re.compile(r'hero:\s*(?P<target>\w+)'), Category.HERO),
    ]

    extract = extract_first_regex_target(regexes)

    assert list(extract('hero: Aino hero: Louhi')) == ['Aino']


def test_extract_all_regex_target_supports_transform():
    regexes = [
        (re.compile(r'number:\s*(?P<target>\d+)'), Category.NUMBER),
    ]

    extract = extract_all_regex_target(regexes, transform=int)

    assert list(extract('number: 3 number: 7')) == [3, 7]


def test_extract_all_regex_target_supports_custom_target_name():
    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.HERO),
    ]

    extract = extract_all_regex_target(regexes, target='name')

    assert list(extract('hero: Aino')) == ['Aino']


def test_extract_all_regex_target_defaults_to_skip_when_target_missing():
    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.HERO),
    ]

    extract = extract_all_regex_target(regexes)

    assert list(extract('hero: Aino')) == []


def test_extract_all_regex_target_missing_none_falls_back_to_category():
    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.HERO),
    ]

    extract = extract_all_regex_target(regexes, missing=None)

    assert list(extract('hero: Aino')) == [Category.HERO]


def test_extract_wrapper_preserves_existing_postprocessors_after_extraction_fallback():
    def classify_louhi(**_):
        return Category.HERO

    regexes = [
        (re.compile(r'hero:\s*(?P<name>\w+)'), Category.UNKNOWN, classify_louhi),
    ]

    extract = extract_all_regex_target(regexes, missing=None)

    assert list(extract('hero: Louhi')) == [Category.HERO]


def test_extract_wrapper_preserves_preprocessors():
    text = 'hero: Aino. hero: Louhi.'

    def second_sentence(text):
        start = text.index('hero: Louhi')
        yield start, len(text)

    regexes = [
        (re.compile(r'hero:\s*(?P<target>\w+)'), Category.HERO, None, second_sentence),
    ]

    extract = extract_all_regex_target(regexes)

    assert list(extract(text)) == ['Louhi']


def test_suppress_overlaps_prevents_later_match_inside_earlier_match():
    regexes = [
        (re.compile(r'not\s+x'), Category.NEGATED_HERO),
        (re.compile(r'x'), Category.HERO),
    ]

    search = search_all_regex(regexes)

    assert list(search('not x')) == [Category.NEGATED_HERO, Category.HERO]
    assert list(search('not x', suppress_overlaps=True)) == [Category.NEGATED_HERO]


def test_suppress_overlaps_allows_non_overlapping_later_matches():
    regexes = [
        (re.compile(r'not\s+x'), Category.NEGATED_HERO),
        (re.compile(r'x'), Category.HERO),
    ]

    search = search_all_regex(regexes)

    assert list(search('not x and x', suppress_overlaps=True)) == [
        Category.NEGATED_HERO,
        Category.HERO,
    ]


def test_suppress_overlaps_preserves_indices():
    regexes = [
        (re.compile(r'not\s+x'), Category.NEGATED_HERO),
        (re.compile(r'x'), Category.HERO),
    ]

    search = search_all_regex(regexes)

    assert [
               (result, match.group(), match.start(), match.end())
               for result, match in search('not x and x', include_match=True, suppress_overlaps=True)
           ] == [
               (Category.NEGATED_HERO, 'not x', 0, 5),
               (Category.HERO, 'x', 10, 11),
           ]


def test_search_first_regex_forwards_suppress_overlaps():
    regexes = [
        (re.compile(r'not\s+x'), Category.NEGATED_HERO),
        (re.compile(r'x'), Category.HERO),
    ]

    search = search_first_regex(regexes)

    assert list(search('not x and x', suppress_overlaps=True)) == [Category.NEGATED_HERO]


def test_get_all_regex_by_index_forwards_suppress_overlaps():
    regexes = [
        (re.compile(r'not\s+x'), Category.NEGATED_HERO),
        (re.compile(r'x'), Category.HERO),
    ]

    get_by_index = get_all_regex_by_index(regexes)

    assert list(get_by_index('not x and x', suppress_overlaps=True)) == [
        (Category.NEGATED_HERO, 'not x', 0, 5),
        (Category.HERO, 'x', 10, 11),
    ]


def test_search_and_replace_compatibility_uses_overlap_suppression():
    regexes = [
        (re.compile(r'not\s+x'), Category.NEGATED_HERO),
        (re.compile(r'x'), Category.HERO),
    ]

    with pytest.warns(DeprecationWarning, match='search_and_replace_regex_func'):
        search = search_and_replace_regex_func(regexes)

    assert list(search('not x and x')) == [
        Category.NEGATED_HERO,
        Category.HERO,
    ]


def test_deprecated_search_all_regex_func_warns_and_delegates():
    regexes = [
        (re.compile(r'Aino'), Category.HERO),
    ]

    with pytest.warns(DeprecationWarning, match='search_all_regex_func'):
        search = search_all_regex_func(regexes)

    assert list(search('Aino')) == [Category.HERO]


def test_deprecated_search_first_regex_func_warns_and_delegates():
    regexes = [
        (re.compile(r'Aino'), Category.HERO),
        (re.compile(r'Louhi'), Category.HERO),
    ]

    with pytest.warns(DeprecationWarning, match='search_first_regex_func'):
        search = search_first_regex_func(regexes)

    assert list(search('Aino Louhi')) == [Category.HERO]


def test_deprecated_search_all_regex_match_func_warns_and_delegates():
    regexes = [
        (re.compile(r'Aino'), Category.HERO),
    ]

    with pytest.warns(DeprecationWarning, match='search_all_regex_match_func'):
        search = search_all_regex_match_func(regexes)

    assert list(search('Aino')) == [Category.HERO]


def test_span_tracker_reports_no_overlap_for_empty_span():
    tracker = SpanTracker()
    tracker.add(1, 5)

    assert tracker.overlaps(3, 3) is False


def test_span_tracker_reports_overlap_with_previous_span():
    tracker = SpanTracker()
    tracker.add(2, 6)

    assert tracker.overlaps(4, 8) is True


def test_span_tracker_reports_overlap_with_next_span():
    tracker = SpanTracker()
    tracker.add(8, 12)

    assert tracker.overlaps(4, 9) is True


def test_span_tracker_allows_adjacent_spans():
    tracker = SpanTracker()
    tracker.add(0, 5)

    assert tracker.overlaps(5, 10) is False


def test_span_tracker_merges_overlapping_spans():
    tracker = SpanTracker()
    tracker.add(0, 5)
    tracker.add(4, 10)

    assert tracker.overlaps(7, 8) is True
    assert tracker.overlaps(10, 12) is False
    assert tracker._spans == [(0, 10)]


def test_span_tracker_merges_adjacent_spans_on_add():
    tracker = SpanTracker()
    tracker.add(0, 5)
    tracker.add(5, 10)

    assert tracker._spans == [(0, 10)]
    assert tracker.overlaps(4, 6) is True
    assert tracker.overlaps(10, 12) is False
