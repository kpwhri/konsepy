import re
from konsepy.rxutils import rx_compile, KonsepyRegex


def test_regex_wrapper_direct_no_dupes():
    pattern = r'(?P<val>\d+)'
    # test without allow_dupe_names 
    rw = KonsepyRegex(pattern, allow_dupe_names=False)
    m = rw.search('123')
    assert m is not None
    assert m.group('val') == '123'
    # should be raw re.Match if no group_mapping
    assert isinstance(m, re.Match)


def test_regex_wrapper_direct_with_dupes():
    pattern = r'(?:(?P<val>A)|(?P<val>B))'
    # test with allow_dupe_names (standard behavior)
    rw = KonsepyRegex(pattern)
    m1 = rw.search('A')
    assert m1.group('val') == 'A'
    m2 = rw.search('B')
    assert m2.group('val') == 'B'
    # should be KonsepyMatch
    from konsepy.rxutils import KonsepyMatch
    assert isinstance(m1, KonsepyMatch)


def test_regex_wrapper_with_compiled_pattern():
    pattern = re.compile(r'(?P<val>\d+)')
    rw = KonsepyRegex(pattern)
    m = rw.search('123')
    assert m.group('val') == '123'
    assert isinstance(m, re.Match)


def test_duplicate_named_groups_alternation():
    pattern = r'(?:score: (?P<val>\d+)|results: (?P<val>\d+))'
    compiled = rx_compile(pattern, re.I)

    # test first branch
    m1 = compiled.search('score: 123')
    assert m1 is not None
    assert m1.group(0) == 'score: 123'
    assert m1.group('val') == '123'
    assert m1.groupdict() == {'val': '123'}
    assert m1.start('val') == 7
    assert m1.end('val') == 10

    # test second branch
    m2 = compiled.search('results: 456')
    assert m2 is not None
    assert m2.group(0) == 'results: 456'
    assert m2.group('val') == '456'
    assert m2.groupdict() == {'val': '456'}
    assert m2.start('val') == 9
    assert m2.end('val') == 12


def test_finditer_returns_wrapped_matches():
    pattern = r'(?:(?P<val>A)|(?P<val>B))'
    compiled = rx_compile(pattern)
    text = 'A B'
    matches = list(compiled.finditer(text))
    assert len(matches) == 2
    assert matches[0].group('val') == 'A'
    assert matches[1].group('val') == 'B'
    assert matches[0].groupdict() == {'val': 'A'}
    assert matches[1].groupdict() == {'val': 'B'}


def test_normal_pattern_behavior():
    pattern = r'(?P<first>\w+) (?P<second>\w+)'
    compiled = rx_compile(pattern)
    m = compiled.search('hello world')
    assert m.group('first') == 'hello'
    assert m.group('second') == 'world'
    assert m.groupdict() == {'first': 'hello', 'second': 'world'}


def test_multiple_duplicates():
    pattern = r'(?P<v>1)|(?P<v>2)|(?P<v>3)'
    compiled = rx_compile(pattern)

    m1 = compiled.search('1')
    assert m1.group('v') == '1'

    m2 = compiled.search('2')
    assert m2.group('v') == '2'

    m3 = compiled.search('3')
    assert m3.group('v') == '3'


def test_group_positional_still_works():
    pattern = r'(?:(?P<val>A)|(?P<val>B))'
    compiled = rx_compile(pattern)
    m = compiled.search('B')
    # internal pattern is (?P<val>A)|(?P<val__dup2>B)
    # group 0: B
    # group 1: None (val)
    # group 2: B (val__dup2)
    assert m.group(0) == 'B'
    assert m.group(1) is None
    assert m.group(2) == 'B'
    assert m.groups() == (None, 'B')


def test_multiple_args_to_group():
    pattern = r'(?P<a>A)|(?P<a>B)'
    compiled = rx_compile(pattern)
    m = compiled.search('B')
    assert m.group(0, 'a') == ('B', 'B')
