"""
Convert downloaded project gutenberg book to jsonl corpus to use as example.

* The `CHAPTER_SPLIT_PAT` may need to be altered to accommodate different books.
* Do not include the table of contents in the path (though this can help with the developing the regex)

Usage:
* `python chapters_to_corpus.py /path/to/gutenberg/book.txt`
    * Outputs: /path/to/gutenberg/book.jsonl
    * Supply to `search.py` along with `patterns.txt`
"""
import json
import re
import sys
from pathlib import Path


CHAPTER_SPLIT_PAT = re.compile(r'^ Chapter (?P<chapter>\d+)\. (?P<title>.*?)$', re.MULTILINE)

def main(path: Path):
    """

    Args:
        path (Path): path to project gutenberg book text (excluding table of contents)

    """
    with open(path, encoding='utf8') as fh:
        text = fh.read()
    # deline the text
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    text = re.sub(r'\n+', '\n', text)

    with open(path.with_suffix('.jsonl'), 'w', encoding='utf8') as out:
        prev = 0
        prev_data = None
        for m in CHAPTER_SPLIT_PAT.finditer(text):
            if prev_data is not None:
                prev_data['text'] = text[prev: m.start() - 1].strip()
                out.write(json.dumps(prev_data) + '\n')
            prev = m.end() + 1
            prev_data = {
                'chapter': m.group('chapter'),
                'title': m.group('title'),
            }

        if prev_data is not None:
            prev_data['text'] = text[prev:].strip()
            out.write(json.dumps(prev_data) + '\n')


if __name__ == '__main__':
    main(Path(sys.argv[1]))
