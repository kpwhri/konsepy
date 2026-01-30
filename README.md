# konsepy

Framework for build NLP information extraction systems using regular expressions. `konsepy` then enables leveraging the NLP system to create a silver standard for fine-tuning a transformer model. 

## Installation

* `konsepy` is designed to be used with the [`knosepy_nlp_template`](https://github.com/kpwhri/konsepy_nlp_template)
  * See the README there for current installation instructions.
* To use `konsepy` as a standalone entity:
  * Install with `pip`:
    * `pip install konsepy[all]`
    * For sentence-splitting corpora from fine-tuning a sentence based transformer, `spacy` will also need to be installed and configured.

## Usage

The package provides a centralized CLI tool `konsepy`.

### Building your NLP Package

To use `konsepy`, you need to create an NLP package (e.g., `my_nlp_package`) with the following structure. The best way to get this format is to clone the [konsepy_nlp_template](https://github.com/kpwhri/konsepy_nlp_template):

```text
my_nlp_package/
├── __init__.py
└── concepts/
    ├── __init__.py
    └── my_concept.py
```

Each concept file (e.g., `my_concept.py`) must define:
* `REGEXES`: A list of regex-category pairs (and optional context functions).
* `RUN_REGEXES_FUNC`: A function that executes the regexes and returns categories/matches.
* `CategoryEnum`: An `Enum` defining the possible categories for the concept.

#### Search Functions

`konsepy` provides several pre-built search functions in `konsepy.rxsearch`:

**Some simple ones:**
- `search_all_regex`: Finds all occurrences of each regex in the list.
- `search_first_regex`: Finds only the first occurrence of each regex.

**Probably the most useful:**
- `search_and_replace_regex_func`: Prevents double-matching by replacing found text with dots before proceeding to the next regex.
- `search_all_regex_func`: Supports "sentinel" values (None) to stop processing if a match was found earlier.

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

#### Custom Search Functions

You can create your own search function by defining a function that returns a generator:

```python
def my_custom_search(regexes):
    def _search(text, include_match=False):
        for regex, category, *other in regexes:
            for m in regex.finditer(text):
                yield (category, m) if include_match else category
    return _search
```

### Running konsepy

```bash
# Run all concepts in a package against input files
konsepy run-all --package-name my_nlp_package --input-files data.csv --outdir output/

# Extract snippets for manual review
konsepy run4snippets --package-name my_nlp_package --input-files data.csv --outdir snippets/

# Generate BIO tagged data for model training
konsepy bio-tag --package-name my_nlp_package --input-files data.csv --outdir bio_data/
```

For more detailed documentation and a template, see [konsepy_nlp_template](https://github.com/kpwhri/konsepy_nlp_template).


## Roadmap

* Change labels to some metadata object to allow more diverse input sources and run info
