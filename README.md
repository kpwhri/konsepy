# konsepy

Framework for build NLP information extraction systems using regular expressions. `konsepy` then enables leveraging the
NLP system to create a silver standard for fine-tuning a transformer model.

## Installation

* `konsepy` is designed to be used with the [`knosepy_nlp_template`](https://github.com/kpwhri/konsepy_nlp_template)
    * See the README there for current installation instructions.
* To use `konsepy` as a standalone entity:
    * Install with `pip`:
        * `pip install konsepy[all]`
        * For sentence-splitting corpora from fine-tuning a sentence based transformer, `spacy` will also need to be
          installed and configured.

## Usage

The package provides a centralized CLI tool `konsepy`.

### Building your NLP Package

To use `konsepy`, you need to create an NLP package (e.g., `my_nlp_package`) with the following structure. The best way
to get this format is to clone the [konsepy_nlp_template](https://github.com/kpwhri/konsepy_nlp_template):

```text
my_nlp_package/
├── __init__.py
└── concepts/
    ├── __init__.py
    └── my_concept.py
```

Each concept file (e.g., `my_concept.py`) must define:

* `REGEXES`: A list of regex-category pairs (and optional context functions).
    * See [Regex Arguments](#regex-arguments)
* `RUN_REGEXES_FUNC`: A function that executes the regexes and returns categories/matches (
  see [search functions, below](#search-functions))
* `CategoryEnum`: An `Enum` defining the possible categories for the concept.

#### Regex Arguments

When defining `REGEXES`, you can supply a variable number of arguments. The can be entirely customized by your
own [search function](#search-functions), but the standard argument list is:

* Position 0: Compile pattern (e.g., `re.compile('score: (?P<val>\d+))`)
* Position 1: Default value (enum) if the compile pattern matches (e.g., `MyCategory.SCORE`)
* Position 2: Post-processing function(s) (use a list/tuple if > 1) (e.g., `[is_negated]`)
    * This function can accept contextual information provided as:
        * m: regex match object
        * precontext: text in `m.start() - window` (default to 20 characters)
        * postcontext: text in `m.end() + window` (default to 20 characters)
        * text: full text
        * window: character window (int)
        * word_window: word window (int)
        * around: text in `m.start() - window to m.end() + window`
* Position 3: Pre-processing function(s) (use a list/tuple if > 1)
    * The functions should return start/end indices of the text that should be processed.
    * They can return (or yield) `None` or `start_index == end_index` if not text should be searched.

## Regex search helpers

`rxsearch` provides small utilities for classifying or extracting values from text
with ordered regex definitions.

The canonical search functions are:

```python
search_all_regex()
search_first_regex()
```

## Regex definition format

Each regex definition may contain up to four positions:

```python
(regex, default_value, postprocessors, preprocessors)
```

### Position 0: regex

A compiled regex pattern.

```python
re.compile(r'score:\s*(?P<target>\d+)')
```

A `None` regex acts as a sentinel. If a non-`UNKNOWN` result has already been
found, searching stops at the sentinel.

```python
REGEXES = [
    (KNOWN_REGEX, 'KNOWN'),
    (None, None),
    (UNKNOWN_REGEX, 'UNKNOWN'),
]
```

### Position 1: default value

The value yielded when the regex matches and no postprocessor overrides or skips
the result.

```python
REGEXES = [
    (re.compile(r'Väinämöinen'), 'HERO'),
]
```

### Position 2: postprocessors

Optional function, list, or tuple of functions.

Postprocessors receive contextual keyword arguments, including:

- `m`: regex match object
- `precontext`: text before the match
- `postcontext`: text after the match
- `text`: full text
- `window`: character context window
- `word_window`: word context window
- `around`: text around the match

A postprocessor may return:

| Return value     | Meaning                                                                      |
|------------------|------------------------------------------------------------------------------|
| `None`           | no override; try the next postprocessor, then fall back to the default value |
| `SKIP`           | skip this match entirely                                                     |
| `value`          | yield `value` instead of the default value                                   |
| `(value, match)` | yield `value` and use `match` for match/index output                         |

Example:

```python
import re

from konsepy.rxsearch import SKIP, search_all_regex


def skip_negated(*, precontext, **_):
    if 'no ' in precontext.lower():
        return SKIP
    return None


REGEXES = [
    (re.compile(r'diabetes'), 'DIABETES', skip_negated),
]

search = search_all_regex(REGEXES)

print(list(search('diabetes')))
print(list(search('no diabetes')))
```

Output:

```python
['DIABETES']
[]
```

### Position 3: preprocessors

Optional function, list, or tuple of functions.

Preprocessor regions are useful when context checks should stay inside a
specific section or sentence.

Preprocessors receive the full text and should return or yield searchable
`(start, end)` regions.

They may return or yield:

- `None`, which is ignored
- `(start, end)`, which is searched
- `(start, start)`, which is ignored

Preprocessor regions also bound context windows. When a match is found inside a
preprocessor region, postprocessors receive `precontext`, `postcontext`, and
`around` values clipped to that region. This applies to both character-based
`window` context and word-based `word_window` context.

If multiple preprocessors or multiple yielded regions overlap, the same text may
be matched more than once. Use `suppress_overlaps=True` if earlier matches should
prevent later overlapping matches from being emitted.

Example:

```python
import re

from konsepy.rxsearch import search_all_regex


def first_sentence_only(text):
    end = text.find('.')
    if end == -1:
        yield 0, len(text)
    else:
        yield 0, end


REGEXES = [
    (
        re.compile(r'score:\s*\d+'),
        'SCORE',
        None,
        first_sentence_only,
    ),
]

search = search_all_regex(REGEXES)

print(list(search('score: 10. score: 20.')))
```

Output:

```python
['SCORE']
```

## Basic classification

Use `search_all_regex()` to yield every matching result.

```python
import re

from konsepy.rxsearch import search_all_regex

REGEXES = [
    (re.compile(r'Väinämöinen'), 'HERO'),
    (re.compile(r'Kalevala'), 'PLACE'),
]

search = search_all_regex(REGEXES)

print(list(search('Väinämöinen sang in Kalevala.')))
```

Output:

```python
['HERO', 'PLACE']
```

```python
import re

from konsepy.rxsearch import search_all_regex


def middle_sentence(text):
    start = text.index('Ilmarinen')
    end = text.index('. Väinämöinen')
    yield start, end


def classify_if_context_stays_in_region(*, precontext, postcontext, around, **_):
    print(precontext)
    print(postcontext)
    print(around)
    return 'HERO'


REGEXES = [
    (
        re.compile(r'forged'),
        None,
        classify_if_context_stays_in_region,
        middle_sentence,
    ),
]

search = search_all_regex(REGEXES, window=100)

print(list(search('Louhi watched. Ilmarinen forged the Sampo. Väinämöinen sang.')))
```

Output:

```python
Ilmarinen
the
Sampo
Ilmarinen
forged
the
Sampo
['HERO']
```

Although `window=100`, the context does not include text before `Ilmarinen` or
after `Sampo` because the preprocessor limited the searchable region.

## First result only

Use `search_first_regex()` to yield at most one result.

```python
import re

from konsepy.rxsearch import search_first_regex

REGEXES = [
    (re.compile(r'Väinämöinen'), 'HERO'),
    (re.compile(r'Kalevala'), 'PLACE'),
]

search = search_first_regex(REGEXES)

print(list(search('Väinämöinen sang in Kalevala.')))
```

Output:

```python
['HERO']
```

## Include match objects

Pass `include_match=True` to receive `(result, match)` tuples.

```python
import re

from konsepy.rxsearch import search_all_regex

REGEXES = [
    (re.compile(r'Väinämöinen'), 'HERO'),
]

search = search_all_regex(REGEXES)

for value, match in search('old Väinämöinen sang', include_match=True):
    print(value, match.group(), match.start(), match.end())
```

Output:

```python
HERO
Väinämöinen
4
15
```

## Return matched text and indices

Use `get_all_regex_by_index()` to yield:

```python
(result, match_text, start, end)
```

Example:

```python
import re

from konsepy.rxsearch import get_all_regex_by_index

REGEXES = [
    (re.compile(r'Väinämöinen'), 'HERO'),
]

get_by_index = get_all_regex_by_index(REGEXES)

print(list(get_by_index('old Väinämöinen sang')))
```

Output:

```python
[('HERO', 'Väinämöinen', 4, 15)]
```

## Extracting `(?P<target>...)`

Use `extract_all_regex_target()` or `extract_first_regex_target()` to return
regex group values instead of default classification values.

By default, these helpers extract the named group `target`.

```python
import re

from konsepy.rxsearch import extract_all_regex_target

REGEXES = [
    (re.compile(r'score:\s*(?P<target>\d+)'), 'SCORE'),
]

extract = extract_all_regex_target(REGEXES)

print(list(extract('score: 10 score: 25')))
```

Output:

```python
['10', '25']
```

## Extract and transform

Use `transform` to convert extracted values.

```python
import re

from konsepy.rxsearch import extract_all_regex_target

REGEXES = [
    (re.compile(r'score:\s*(?P<target>\d+)'), 'SCORE'),
]

extract = extract_all_regex_target(REGEXES, transform=int)

print(list(extract('score: 10 score: 25')))
```

Output:

```python
[10, 25]
```

Falsey transformed values, such as `0`, are preserved.

```python
print(list(extract('score: 0')))
```

Output:

```python
[0]
```

## Extract a different group

Use `target` to extract a different group name or group index.

```python
import re

from konsepy.rxsearch import extract_all_regex_target

REGEXES = [
    (re.compile(r'hero:\s*(?P<name>\w+)'), 'HERO'),
]

extract = extract_all_regex_target(REGEXES, target='name')

print(list(extract('hero: Aino')))
```

Output:

```python
['Aino']
```

## Configure extraction fallback

Extraction skips matches by default when the group is missing or unmatched.

```python
from konsepy.rxsearch import SKIP

extract = extract_all_regex_target(
    REGEXES,
    missing=SKIP,
    unmatched=SKIP,
)
```

To fall back to the regex default value, use `None`.

```python
extract = extract_all_regex_target(
    REGEXES,
    missing=None,
    unmatched=None,
)
```

If extraction returns `None`, later postprocessors may still run. If no
postprocessor returns a value, the default value is yielded.

Extraction is handled before postprocessors.

When using `extract_all_regex_target()` or `extract_first_regex_target()`, the
extracted value is passed to postprocessors as:

- `extracted`
- `extracted_value`
- `extracted_precontext`: precontext started at the target
- `extracted_postcontext`: postcontext started at the target
- `extracted_around`: precontext and postcontext started at the target

Extracted context uses the same `window` or `word_window` settings as match
context. If the regex was found inside a preprocessor region, extracted context
is also clipped to that region.

If a postprocessor returns `None`, the extracted value is returned.

If a postprocessor returns `SKIP`, the match is skipped.

If a postprocessor returns any other value, that value replaces the extracted
value.

For extraction helpers, target context is centered on the extracted group rather
than the whole regex match.

```python
import re

from konsepy.rxsearch import extract_all_regex_target


def score_sentence(text):
    start = text.index('score')
    end = text.index('. Väinämöinen')
    yield start, end


def inspect_context(*, extracted, extracted_precontext, extracted_postcontext, **_):
    print(extracted)
    print(extracted_precontext)
    print(extracted_postcontext)
    return None


REGEXES = [
    (
        re.compile(r'score:\s*(?P<target>\d+)'),
        None,
        inspect_context,  # postprocessor
        score_sentence,  # preprocessor
    ),
]

extract = extract_all_regex_target(REGEXES, transform=int, window=100)

print(list(extract('Louhi watched. score: 3. Väinämöinen sang.')))
```

Output:

```python
3
score:

[3]
```

The extracted precontext is `score: `, not `Louhi watched. score: `, because the
preprocessor region begins at `score`.

## Use extraction as a postprocessor

Use `extract_group()` directly in position 2 when you want extraction behavior
inside regular `search_all_regex()` or `search_first_regex()` calls.

```python
import re

from konsepy.rxsearch import extract_group, search_all_regex

REGEXES = [
    (
        re.compile(r'score:\s*(?P<target>\d+)'),
        'SCORE',
        extract_group(),
    ),
]

search = search_all_regex(REGEXES)

print(list(search('score: 10')))
```

Output:

```python
['10']
```

Use `extract_group_as()` to transform the group.

```python
import re

from konsepy.rxsearch import extract_group_as, search_all_regex

REGEXES = [
    (
        re.compile(r'score:\s*(?P<target>\d+)'),
        'SCORE',
        extract_group_as(transform=int),
    ),
]

search = search_all_regex(REGEXES)

print(list(search('score: 10')))
```

Output:

```python
[10]
```

## Labeled extraction results

Extraction concepts can return an enum label plus an extracted value. This lets
classification and extraction concepts appear similarly in category count files,
while still preserving extracted values in separate extraction files. The enum
label is optional: if you omit it, extraction returns raw values only. If you
include it (either via a postprocessor or by setting the category position in
`REGEXES`), the system automatically wraps extracted values in
`ExtractionResult`.

```python
import enum
import re

from konsepy.results import ExtractionResult
from konsepy.rxsearch import extract_all_regex_target


class ScoreCategory(enum.Enum):
    SCORE = 1
    UNKNOWN = -1


REGEXES = [
    (
        re.compile(r'\bscore\s*:\s*(?P<target>\d+)\b', re.I),
        ScoreCategory.SCORE,
    ),
]

RUN_REGEXES_FUNC = extract_all_regex_target(REGEXES, transform=int)
```

The standard category output counts `ScoreCategory.SCORE`. Extraction-specific
outputs store the numeric value.

## Prevent overlapping duplicate matches

Pass `suppress_overlaps=True` to let earlier matches claim spans of text.
Later matches that overlap already-claimed spans are skipped.

This is useful when a specific pattern should override a more general one.

```python
import re

from konsepy.rxsearch import search_all_regex

REGEXES = [
    (re.compile(r'not\s+x'), 'NEGATED_X'),
    (re.compile(r'x'), 'X'),
]

search = search_all_regex(REGEXES)
search_suppress = search_all_regex(REGEXES, suppress_overlaps=True)

print(list(search('not x')))
print(list(search_suppress('not x')))
```

Output:

```python
['NEGATED_X', 'X']
['NEGATED_X']
```

The original text is not modified, so match indices and context windows remain
stable.

Non-overlapping later matches are still returned.

```python
print(list(search_suppress('not x and x')))
```

Output:

```python
['NEGATED_X', 'X']
```

## Ignore preprocessing regions

Pass `ignore_indices=True` to search the whole text even when preprocessors are
defined. This is mainly useful in tests.

When `ignore_indices=True`, preprocessor regions are not used for searching or
for context clipping. Postprocessors receive full-text context limited only by
`window` or `word_window`.

```python
import re

from konsepy.rxsearch import search_all_regex


def no_regions(text):
    return None


REGEXES = [
    (
        re.compile(r'Väinämöinen'),
        'HERO',
        None,
        no_regions,
    ),
]

search = search_all_regex(REGEXES)

print(list(search('Väinämöinen')))
print(list(search('Väinämöinen', ignore_indices=True)))
```

Output:

```python
[]
['HERO']
```

## Deprecated compatibility names

Use these names for new code:

```python
search_all_regex()
search_first_regex()
```

These older names remain available for compatibility, but emit
`DeprecationWarning`:

```python
search_all_regex_func()
search_first_regex_func()
search_all_regex_match_func()
search_and_replace_regex_func()
```

`search_and_replace_regex_func()` now delegates to overlap-suppressed search
instead of modifying the searched text. Prefer:

```python
search = search_all_regex(REGEXES, suppress_overlaps=True)

results = list(search(text))
```

## Regex Utilities

`konsepy` includes `KonsepyRegex` in `konsepy.rxutils` to allow for duplicate named groups in alternation branches:

```python
import re
from konsepy.rxutils import KonsepyRegex

pattern = KonsepyRegex(
    r'(?:score: (?P<val>\d+)|results: (?P<val>\d+))',
    flags=re.I,
    allow_dupe_names=True,
)
# m.group("val") will return whichever branch matched
```

You can also use the shorthand helper `rx_compile`:

```python
from konsepy.rxutils import rx_compile

pattern = rx_compile(r'(?:this: (?P<val>\d+)|results: (?P<val>\d+))')
```

Example of `my_concept.py`:

```python
import re
from enum import Enum
from konsepy.rxsearch import search_all_regex_func
from konsepy.context.negation import check_if_negated
from konsepy.context.other_subject import check_if_other_subject


class CategoryEnum(Enum):
    MENTION = 1
    NO = 0
    OTHER = 3


REGEXES = [
    (re.compile(r'my pattern', re.I),
     CategoryEnum.MENTION,
     [
         lambda **kwargs: check_if_negated(neg_concept=CategoryEnum.NO, **kwargs),
         lambda **kwargs: check_if_other_subject(other_concept=CategoryEnum.OTHER, **kwargs),
     ]
     ),
]

# word_window specifies the number of words to retrieve for context functions (instead of character):
RUN_REGEXES_FUNC = search_all_regex_func(REGEXES, word_window=5)
# to alter the character-based window:
RUN_REGEXES_FUNC = search_all_regex_func(REGEXES, window=50)  # defaults to 30
```

## Custom Search Functions

You can create your own search function by defining a function that returns a generator:

```python
def my_custom_search(regexes):
    def _search(text, include_match=False):
        for regex, category, *other in regexes:
            for m in regex.finditer(text):
                yield (category, m) if include_match else category

    return _search
```

## Running konsepy

```bash
# Run all concepts in a package against input files
konsepy run-all --package-name my_nlp_package --input-files data.csv --outdir output/

# Run and output individual matches as JSONL (useful for match-level analysis)
konsepy run-all-matches --package-name my_nlp_package --input-files data.csv --outdir output/

# Extract snippets for manual review
konsepy run4snippets --package-name my_nlp_package --input-files data.csv --outdir snippets/

# Generate BIO tagged data for model training
konsepy bio-tag --package-name my_nlp_package --input-files data.csv --outdir bio_data/
```

For more detailed documentation and a template,
see [konsepy_nlp_template](https://github.com/kpwhri/konsepy_nlp_template).

## Testing

```bash
# end-to-end BIO train/predict test (requires a local model path)
python -m pytest test/test_train_predict_e2e.py -k test_train_predict_e2e --bio-model-path /my/huggingface/models/roberta-base
```

**Note**: By default, prediction output merges adjacent subword spans that share the same
entity label into a single result to produce word-level captures. To preserve
raw token-level spans for debugging, pass `--no-merge-subwords` to the
prediction CLI.

## Roadmap

* Change labels to some metadata object to allow more diverse input sources and run info
