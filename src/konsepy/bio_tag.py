"""
Usage: python bio_tag.py --outdir /path/to/output --infiles infile.csv infile.sas7bdat

Post-processing:
* Identify which `count`/index values should be removed based on noise rules
* Remove these from the output jsonl file

"""

import csv
import json
from pathlib import Path

import spacy

from konsepy.cli import add_outdir_and_infiles
from konsepy.constants import NOTETEXT_LABEL, NOTEDATE_LABEL, NOTEID_LABEL, ID_LABEL
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file
from konsepy.types import RegexDict


def format_for_spacy(row_iter):
    for count, studyid, note_id, note_date, text in row_iter:
        yield text, (count, studyid, note_id, note_date)


def get_pipeline(sentence_model, spacy_model='en_core_web_sm'):
    if sentence_model == 'senter':
        nlp = spacy.load(spacy_model,
                         disable=('tok2vec', 'tagger', 'attribute_ruler', 'lemmatizer', 'ner', 'parser'))
        nlp.enable_pipe('senter')
    elif sentence_model == 'parser':
        nlp = spacy.load(spacy_model, disable=('tagger', 'attribute_ruler', 'lemmatizer', 'ner'))
    else:
        raise ValueError(f'Unrecognized `sentence_model`: {sentence_model}.')
    return nlp


def build_regex_dict(package_name):
    if not package_name:
        raise ValueError('Specify name of package.')
    return {concept.name: concept.run_func for concept in get_all_concepts(package_name)}


def get_bio_tags(input_files, outdir: Path, *, package_name: str = None, regexes: RegexDict = None,
                 sentence_model='senter',
                 id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                 notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                 noteorder_label=None):
    """

    """
    outdir.mkdir(exist_ok=True)

    # prepare sentence splitter
    nlp = get_pipeline(sentence_model)

    if not package_name and not regexes:
        raise ValueError(f'Either `regexes` or `package_name` must be specified.')
    regexes = regexes or build_regex_dict(package_name)

    with (
        open(outdir / 'bio_tag_data.csv', 'w', newline='') as out,
        open(outdir / 'bio_tag_data.jsonl', 'w') as jsonl,
    ):
        writer = csv.DictWriter(
            out,
            fieldnames=['index', 'studyid', 'note_id', 'sentence_id', 'domain', 'category', 'capture', 'start', 'end']
        )
        writer.writeheader()
        i = 0
        for doc, (count, studyid, note_id, note_date) in nlp.pipe(format_for_spacy(
                iterate_csv_file(
                    input_files, id_label=id_label, noteid_label=noteid_label, notedate_label=notedate_label,
                    notetext_label=notetext_label, noteorder_label=noteorder_label,
                )
        ), as_tuples=True):
            constant_meta = {
                'studyid': studyid,
                'note_id': note_id,
            }
            for sent_id, sentence in enumerate(doc.sents):
                sentence = str(sentence)
                curr_note = {  # records for this text note
                    'results': [],
                    'text': sentence,
                    'sentence_id': sent_id,
                }
                for domain, regex_func in regexes.items():
                    for category, capture, start, end in regex_func(sentence):
                        data = {
                            'index': i,
                            'domain': domain,
                            'category': category,
                            'capture': capture,
                            'start': start,
                            'end': end,
                        }
                        writer.writerow(data | constant_meta | {'sentence_id': sent_id})
                        curr_note['results'].append(data)
                        i += 1
                # write 1 line per input sentence
                curr_note['results'] = sorted(curr_note['results'], key=lambda x: x['start'])
                jsonl.write(json.dumps(constant_meta | curr_note) + '\n')


if __name__ == '__main__':
    get_bio_tags(**vars(add_outdir_and_infiles().parse_args()))
