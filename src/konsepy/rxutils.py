import re
from typing import Dict, List, Union


class KonsepyMatch:
    """Wrapper for re.Match that handles duplicate named groups."""

    def __init__(self, match: re.Match, group_mapping: Dict[str, List[str]]):
        self._match = match
        self._group_mapping = group_mapping

    def group(self, *args):
        """Proxy group() and handle synthesized names."""
        if not args:
            return self._match.group(0)

        results = []
        for arg in args:
            if isinstance(arg, str) and arg in self._group_mapping:
                # find first internal group that matched
                found = False
                for internal_name in self._group_mapping[arg]:
                    val = self._match.group(internal_name)
                    if val is not None:
                        results.append(val)
                        found = True
                        break
                if not found:
                    results.append(None)
            else:
                results.append(self._match.group(arg))

        if len(results) == 1:
            return results[0]
        return tuple(results)

    def groups(self, default=None):
        """Proxy groups()."""
        return self._match.groups(default)

    def groupdict(self, default=None):
        """Proxy groupdict() and collapse duplicate names."""
        raw_dict = self._match.groupdict(default)
        collapsed = {}
        for original_name, internal_names in self._group_mapping.items():
            for internal_name in internal_names:
                val = raw_dict.get(internal_name)
                if val is not None:
                    collapsed[original_name] = val
                    break
            else:
                collapsed[original_name] = default
        return collapsed

    def start(self, group=0):
        """Proxy start()."""
        if isinstance(group, str) and group in self._group_mapping:
            for internal_name in self._group_mapping[group]:
                if self._match.group(internal_name) is not None:
                    return self._match.start(internal_name)
        return self._match.start(group)

    def end(self, group=0):
        """Proxy end()."""
        if isinstance(group, str) and group in self._group_mapping:
            for internal_name in self._group_mapping[group]:
                if self._match.group(internal_name) is not None:
                    return self._match.end(internal_name)
        return self._match.end(group)

    def span(self, group=0):
        """Proxy span()."""
        if isinstance(group, str) and group in self._group_mapping:
            for internal_name in self._group_mapping[group]:
                if self._match.group(internal_name) is not None:
                    return self._match.span(internal_name)
        return self._match.span(group)

    def __getattr__(self, name):
        """Forward any other attributes to the original match object."""
        return getattr(self._match, name)


class KonsepyRegex:
    """Wrapper for compiled regex that handles optional duplicate named groups."""

    def __init__(self, pattern: Union[str, re.Pattern], flags: int = 0, allow_dupe_names: bool = True):
        self._group_mapping = {}
        if allow_dupe_names and isinstance(pattern, str):
            # find all (?P<name>...)
            named_group_re = re.compile(r'\(\?P<(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>')

            group_counts = {}

            def rename_match(m):
                name = m.group('name')
                if name not in group_counts:
                    group_counts[name] = 1
                    internal_name = name
                else:
                    group_counts[name] += 1
                    internal_name = f'{name}__dup{group_counts[name]}'

                if name not in self._group_mapping:
                    self._group_mapping[name] = []
                self._group_mapping[name].append(internal_name)

                return f'(?P<{internal_name}>'

            pattern = named_group_re.sub(rename_match, pattern)

        if isinstance(pattern, str):
            self._pattern = re.compile(pattern, flags)
        else:
            self._pattern = pattern

    def finditer(self, string: str, pos: int = 0, endpos: int = 2147483647):
        """Proxy finditer() and wrap results."""
        for m in self._pattern.finditer(string, pos, endpos):
            yield KonsepyMatch(m, self._group_mapping) if self._group_mapping else m

    def search(self, string: str, pos: int = 0, endpos: int = 2147483647):
        """Proxy search() and wrap result."""
        m = self._pattern.search(string, pos, endpos)
        if not m:
            return None
        return KonsepyMatch(m, self._group_mapping) if self._group_mapping else m

    def match(self, string: str, pos: int = 0, endpos: int = 2147483647):
        """Proxy match() and wrap result."""
        m = self._pattern.match(string, pos, endpos)
        if not m:
            return None
        return KonsepyMatch(m, self._group_mapping) if self._group_mapping else m

    def fullmatch(self, string: str, pos: int = 0, endpos: int = 2147483647):
        """Proxy fullmatch() and wrap result."""
        m = self._pattern.fullmatch(string, pos, endpos)
        if not m:
            return None
        return KonsepyMatch(m, self._group_mapping) if self._group_mapping else m

    def __getattr__(self, name):
        """Forward any other attributes to the original pattern object."""
        return getattr(self._pattern, name)


def rx_compile(pattern: str, flags: int = 0) -> KonsepyRegex:
    r"""
    Compile a regex pattern, allowing duplicate named groups in alternation branches.

    Example:
        compile_pattern_allow_dupe_names(r'(?:score: (?P<val>\d+)|results: (?P<val>\d+))')
    """
    return KonsepyRegex(pattern, flags=flags, allow_dupe_names=True)


class RxType(type):
    MAPPING = {
        'p': '.',
        'w': r'\w',
        'W': r'\W',
        'S': r'\S',
        's': r'\s',
        'o': r'(?:\w+\W*)',  # word
    }

    def __getattr__(cls, item):
        return cls._parse_item(item)

    def _parse_item(cls, element):
        el = cls.MAPPING[element[0]]
        if len(element) > 1:
            return el + cls._parse_numbers(*element[1:].split('_'))
        return el

    def _parse_numbers(cls, *nums):
        if len(nums) == 1:
            v1 = 0
            v2 = nums[0]
        else:
            v1, v2 = nums
        return rf'{{{v1},{v2}}}'


class Rx(metaclass=RxType):
    pass
