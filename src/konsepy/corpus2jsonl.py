import datetime
import json
from collections import Counter
from pathlib import Path

from loguru import logger

from konsepy.bio_tag_sentence import get_pipeline
from konsepy.cli import add_outdir_and_infiles
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.textio import iterate_csv_file


def get_target_overlap(sentences: list[tuple[int, str]], max_previous):
    """Determine how many sentences can be retained to provide additional context."""
    if len(sentences) == 1:
        return 2, [], 0  # if only a single sentence, don't include in next window
    total_length = 0
    total_char_length = 0
    for i, (length, sentence) in enumerate(sentences[::-1]):
        if total_length + length >= max_previous:
            if i == 0 and length > max_previous * 2:
                return 2, [], 0  # previous sentence is too long
            return length + 2, sentences[min(-1, -i):], total_char_length
        total_length += length
        total_char_length += len(sentence)
    return total_length + 2, sentences[-1:], total_char_length  # just the last sentence


def corpus2jsonl(input_files, outdir: Path, *,
                 split=None, max_seq_length=512, tokenizer=None,
                 sentence_model='senter',
                 id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                 notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                 noteorder_label=None, metadata_labels=None, encoding='utf8',
                 limit_noteids=None):
    """
    Convert a corpus to a jsonl format, suitable for using prodigy
    """
    if split in {'sentence', 'sent_chunk', 'sent_window'}:
        nlp = get_pipeline(sentence_model)
    if split in {'sent_chunk', 'sent_window'}:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(tokenizer)
    start_time = datetime.datetime.now()
    dt = start_time.strftime("%Y%m%d_%H%M%S")
    if split is not None:
        name = f'corpus_{dt}.{split}.jsonl'
    else:
        name = f'corpus_{dt}.jsonl'
    length_counter = Counter()
    with open(outdir / name, 'w', encoding='utf8') as out:
        for count, studyid, note_id, note_date, text, metadata in iterate_csv_file(
                input_files, encoding=encoding,
                id_label=id_label, noteid_label=noteid_label,
                notedate_label=notedate_label, notetext_label=notetext_label,
                noteorder_label=noteorder_label, metadata_labels=metadata_labels,
        ):
            if limit_noteids and note_id not in limit_noteids:
                continue
            if split is None:
                out.write(json.dumps({
                    'id': count,
                    'studyid': studyid,
                    'note_id': note_id,
                    'note_date': note_date,
                    'start_index': 0,
                    'end_index': len(text),
                    'text': text,
                }) + '\n')
            elif split == 'sentence':
                doc = nlp(text)
                for sent_id, spacy_sentence in enumerate(doc.sents):
                    sentence = str(spacy_sentence)
                    out.write(json.dumps({
                        'id': count,
                        'studyid': studyid,
                        'note_id': note_id,
                        'note_date': note_date,
                        'sentence_id': sent_id,
                        'start_index': spacy_sentence.start_char,
                        'end_index': spacy_sentence.end_char,
                        'text': sentence,
                    }) + '\n')
            elif split == 'section':
                raise NotImplementedError
            elif split == 'sent_chunk':
                doc = nlp(text)
                sents = list(doc.sents)
                chunk_id = 0
                curr = []
                curr_length = 2  # start/end
                start_index = 0  # approximate character index from start
                end_index = None
                for sent_id, spacy_sentence in enumerate(sents):
                    sentence = str(spacy_sentence)
                    length = len(tokenizer.tokenize(sentence))  # if len(sent) > max_seq_length, allow truncation
                    if length + curr_length > max_seq_length:
                        # TODO: what if curr_length == 0 (i.e., len(sentence) > max_seq_length)?
                        out.write(json.dumps({
                            'id': count,
                            'studyid': studyid,
                            'note_id': note_id,
                            'note_date': note_date,
                            'chunk_id': chunk_id,
                            'start_index': start_index,
                            'end_index': end_index,
                            'text': ' '.join(curr),  # sentences retain their punctuation chars, but not spaces
                        }) + '\n')
                        # reset vars
                        chunk_id += 1
                        curr = [sentence]
                        curr_length = 2 + length
                        start_index = spacy_sentence.start_char
                        end_index = spacy_sentence.end_char
                    else:
                        length_counter[length] += 1
                        curr.append(sentence)
                        curr_length += length
                        end_index = spacy_sentence.end_char
                        if spacy_sentence[-1].is_space and spacy_sentence[-1].text.count('\n') > 1:
                            # end of a section/paragraph
                            out.write(json.dumps({
                                'id': count,
                                'studyid': studyid,
                                'note_id': note_id,
                                'note_date': note_date,
                                'chunk_id': chunk_id,
                                'start_index': start_index,
                                'end_index': end_index,
                                'text': ' '.join(curr),  # sentences retain their punctuation chars
                            }) + '\n')
                            # reset vars
                            chunk_id += 1
                            curr = []
                            curr_length = 2
                            start_index = spacy_sentence.end_char
                # final fencepost
                if curr:
                    out.write(json.dumps({
                        'id': count,
                        'studyid': studyid,
                        'note_id': note_id,
                        'note_date': note_date,
                        'chunk_id': chunk_id,
                        'start_index': start_index,
                        'end_index': end_index,
                        'text': ' '.join(curr),  # sentences retain their punctuation chars
                    }) + '\n')
            elif split == 'sent_window':
                target_overlap = int(max_seq_length / 4)
                doc = nlp(text)
                sents = list(doc.sents)
                chunk_id = 0
                curr = []  # tuple(length: int, sentence: str)
                curr_length = 2  # start/end
                start_index = 0
                end_index = None
                for sent_id, spacy_sentence in enumerate(sents):
                    sentence = str(spacy_sentence)
                    length = len(tokenizer.tokenize(sentence))  # if len(sent) > max_seq_length, allow truncation
                    if length + curr_length > max_seq_length:
                        out.write(json.dumps({
                            'id': count,
                            'studyid': studyid,
                            'note_id': note_id,
                            'note_date': note_date,
                            'chunk_id': chunk_id,
                            'start_index': start_index,
                            'end_index': end_index,
                            'text': ' '.join(c for _, c in curr),  # sentences retain their punctuation chars
                        }) + '\n')
                        # reset vars
                        chunk_id += 1
                        curr_length, curr, char_length = get_target_overlap(curr, target_overlap)
                        curr.append((length, sentence))
                        curr_length = 2 + length
                        start_index = spacy_sentence.start_char - char_length  # this is the next sentence - overlap
                        end_index = spacy_sentence.end_char
                    else:
                        length_counter[length] += 1
                        curr.append((length, sentence))
                        curr_length += length
                        end_index = spacy_sentence.end_char
                        if spacy_sentence[-1].is_space and spacy_sentence[-1].text.count('\n') > 1:
                            # end of a section/paragraph
                            out.write(json.dumps({
                                'id': count,
                                'studyid': studyid,
                                'note_id': note_id,
                                'note_date': note_date,
                                'chunk_id': chunk_id,
                                'start_index': start_index,
                                'end_index': end_index,
                                'text': ' '.join(c for _, c in curr),  # sentences retain their punctuation chars
                            }) + '\n')
                            # reset vars
                            chunk_id += 1
                            curr_length, curr, char_length = get_target_overlap(curr, target_overlap)
                            start_index = spacy_sentence.end_char + 1 - char_length  # this sentence - overlap
                # final fencepost
                if curr:
                    out.write(json.dumps({
                        'id': count,
                        'studyid': studyid,
                        'note_id': note_id,
                        'note_date': note_date,
                        'chunk_id': chunk_id,
                        'start_index': start_index,
                        'end_index': end_index,
                        'text': ' '.join(c for _, c in curr),  # sentences retain their punctuation chars
                    }) + '\n')
            else:
                raise ValueError(f'Unrecognized option for splitting: {split}')
            if count % 50000 == 0:
                logger.info(f'Completed {count:,} records ({datetime.datetime.now()})')
    end_time = datetime.datetime.now()
    if length_counter:
        logger.info(f'Too long so truncated: {len(length_counter)}')
        logger.info(f' * {sorted(length_counter, reverse=True)[:5]}')
    logger.info(f'DONE: Completed {count:,} records ({end_time})')
    logger.info(f'DONE: Total processing time: {end_time - start_time}.')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    add_outdir_and_infiles(parser)
    parser.add_argument('--split', default=None,
                        choices=['sentence', 'section', 'sent_chunk', 'sent_window'],
                        help='How to split/divide the text. Defaults to None (i.e., keep entire text together).')
    parser.add_argument('--max-seq-length', dest='max_seq_length', default=512, type=int,
                        help='Number of tokens to retain when `--split` is sent_chunk or sent_window.')
    parser.add_argument('--tokenizer', default=None,
                        help='Path to BERT tokenizer.')
    corpus2jsonl(**vars(parser.parse_args()))
