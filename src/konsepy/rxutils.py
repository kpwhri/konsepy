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
