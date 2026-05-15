"""
Utilities for testing.
"""

def check_pattern(sentence, expected_val, *patterns, group_label='target'):
    """Checks if any pattern in pattern_list matches the sentence and captures expected_val.

    Usage:
        # use with KonsepyRegex to explore results
        @pytest.mark.parametrize('text, expected_val', [
            ('AHI 4% of 11.0/hour', '11.0'),
        ])
        def test_patterns(text, expected_val):
            assert check_pattern(text, expected_val, PATTERN)
    """
    found = False
    for pat in patterns:
        m = pat.search(sentence)
        if m and 'target' in m.groupdict():
            if m.group('target') == str(expected_val):
                found = True
                break
            else:
                print(f'Found unexpected: {m.group("target")}.')
        print(f'Pattern not found: {pat}')
    return found
