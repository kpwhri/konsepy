import argparse
import datetime
import json
from pathlib import Path
from datasets import Dataset, Sequence
from konsepy.cli import clean_args
from loguru import logger


def get_spans(spans):
    """Get start, end, and domain (i.e., tag)"""
    for span in spans:
        yield span['start'], span['end'], span['domain'], False


def update_word(i, tokens, ner_tags, curr_word, span_start, span_is_middle, span_tag):
    tokens.append(''.join(curr_word))
    if i >= span_start:
        if span_is_middle:
            ner_tags.append(f'I-{span_tag}')
        else:
            ner_tags.append(f'B-{span_tag}')
            span_is_middle = True
    else:
        ner_tags.append('O')
    return span_is_middle


def create_bio_dataset(path: Path, outpath: Path, test_size=0.1, validation_size=0.05, note_id_field='note_id'):
    """Convert jsonl file into a datasets.DatasetDict for use in model building.

    path: path to jsonl file generated by `bio_tag.py`
    outpath: path to place dataset
    test_size: size of test set (default: 0.05)
    validation_size: size of validation set (default: 0.1)
    note_id_field: name of field containing unique identifier to the note/document (default: note_id)
    """
    all_note_ids = []
    all_tokens = []
    all_ner_tags = []
    with open(path, encoding='utf8') as fh:
        for line in fh:
            data = json.loads(line.strip())
            tokens = []
            ner_tags = []
            spans = get_spans(data['results'])
            span_start, span_end, span_tag, span_is_middle = next(spans)

            curr_word = []
            for i, letter in enumerate(data['text']):
                if letter == ' ':  # end of word
                    if curr_word:
                        span_is_middle = update_word(
                            i, tokens, ner_tags, curr_word, span_start,
                            span_is_middle, span_tag,
                        )
                        curr_word = []
                elif letter.isalpha():
                    curr_word.append(letter)
                else:  # punctuation
                    if curr_word:
                        span_is_middle = update_word(
                            i, tokens, ner_tags, curr_word, span_start,
                            span_is_middle, span_tag,
                        )
                        curr_word = []
                    tokens.append(letter)
                    ner_tags.append('O')
                if i >= span_end:
                    try:
                        span_start, span_end, span_tag, span_is_middle = next(spans)
                    except StopIteration:
                        span_start, span_end = 100_000, 100_000
            if curr_word:
                update_word(
                    i, tokens, ner_tags, curr_word, span_start,
                    span_is_middle, span_tag,
                )
            all_note_ids.append(data[note_id_field])
            all_tokens.append(tokens)
            all_ner_tags.append(ner_tags)

    tagset = set([x for el in all_ner_tags for x in el])
    logger.info(f'Tagset of length {len(tagset)}: {",".join(tagset)}')

    ds = Dataset.from_dict({
        'tokens': Sequence(features=all_tokens),
        'ner_tags': Sequence(features=all_ner_tags),
        'note_ids': all_note_ids,
    })

    res = ds.train_test_split(validation_size, shuffle=True)
    length = len(all_note_ids)
    num = length - (length * validation_size)
    denom = length * test_size
    ds = res['train'].train_test_split(test_size=num / denom, shuffle=True)
    ds['validation'] = res['test']
    ds.save_to_disk(outpath / f'{path.stem}.{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.dataset')


def create_bio_dataset_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('path', type=Path,
                        help='Path to jsonl input file.')
    parser.add_argument('outpath', type=Path,
                        help='Path to write created dataset.')
    parser.add_argument('--test-size', dest='test_size', type=float, default=0.1,
                        help='Percent of data to use for testing.')
    parser.add_argument('--validation-size', dest='validation_size', type=float, default=0.05,
                        help='Percent of data to hold out for final validation.')
    parser.add_argument('--note-id-field', dest='note_id_field', type=str, default='note_id',
                        help='Specify label in jsonl file for distinguishing unique documents/notes.')
    create_bio_dataset(**clean_args(vars(parser.parse_args())))


if __name__ == '__main__':
    create_bio_dataset_args()
