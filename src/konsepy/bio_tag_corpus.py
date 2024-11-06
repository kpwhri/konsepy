"""
Get biotags for a corpus.

Usage: python bio_tag.py --outdir /path/to/output --infiles infile.csv infile.sas7bdat

Post-processing:
* Identify which `count`/index values should be removed based on noise rules
* Remove these from the output jsonl file

"""

import csv
import json
from pathlib import Path

from konsepy.cli import add_outdir_and_infiles, concept_cli
from konsepy.constants import NOTETEXT_LABEL, NOTEDATE_LABEL, NOTEID_LABEL, ID_LABEL
from konsepy.importer import get_all_concepts
from konsepy.types import RegexDict


def build_regex_dict(package_name, concepts):
    if not package_name:
        raise ValueError('Specify name of package.')
    return {concept.name: concept.run_func for concept in get_all_concepts(package_name, *concepts or list())}


def get_bio_tags_corpus(input_files, outdir: Path, *, package_name: str = None,
                        concepts=None, regexes: RegexDict = None,
                        id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                        notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                        noteorder_label=None, **kwargs):
    """

    """
    outdir.mkdir(exist_ok=True)

    if not package_name and not regexes:
        raise ValueError(f'Either `regexes` or `package_name` must be specified.')
    regexes = regexes or build_regex_dict(package_name, concepts)

    fieldnames = ['index', 'id', 'studyid', 'note_id', 'chunk_id', 'domain', 'category', 'capture', 'start', 'end']

    with (
        open(outdir / 'bio_tag_data.corpus.csv', 'w', newline='') as out,
        open(outdir / 'bio_tag_data.corpus.jsonl', 'w') as jsonl,
    ):
        writer = csv.DictWriter(out, fieldnames=fieldnames)
        writer.writeheader()
        i = 0
        for jsonl_file in input_files:
            with open(jsonl_file, encoding='utf8') as fh:
                for line in fh:
                    data = json.loads(line.strip())
                    extras = {'chunk_start': data['start_index']}
                    if 'sentence_id' in data:
                        extras['chunk_id'] = data['sentence_id']
                    data['results'] = []
                    for domain, regex_func in regexes.items():
                        for category, (capture, start, end) in zip(regex_func(data['text'])):
                            curr_data = {
                                'index': i,
                                'domain': domain,
                                'category': category,
                                'capture': capture,
                                'start': start,
                                'end': end,
                            }
                            writer.writerow(
                                {k: v for k, v in (data | curr_data | extras).items()
                                 if k in fieldnames})
                            data['results'].append(curr_data)
                            i += 1
                        # write 1 line per input sentence
                        data['results'] = sorted(data['results'], key=lambda x: x['start'])
                        jsonl.write(json.dumps(data) + '\n')


if __name__ == '__main__':
    concept_cli(get_bio_tags_corpus)
