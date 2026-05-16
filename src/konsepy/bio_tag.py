"""
Usage: python bio_tag.py --outdir /path/to/output --infiles infile.csv infile.sas7bdat

Post-processing:
* Identify which `count`/index values should be removed based on noise rules
* Remove these from the output jsonl file

"""

import csv
import json
from pathlib import Path

from loguru import logger

from konsepy.cli import concept_cli
from konsepy.constants import NOTETEXT_LABEL, NOTEDATE_LABEL, NOTEID_LABEL, ID_LABEL
from konsepy.engine import ProcessingEngine
from konsepy.results import get_result_label


def get_bio_tags(input_files, outdir: Path, *, package_name: str = None,
                 id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                 notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                 noteorder_label=None, metadata_labels=None,
                 concepts=None, **kwargs):
    """
    Generate BIO tagged data using ProcessingEngine.
    """
    outdir.mkdir(exist_ok=True)

    if not package_name:
        raise ValueError('`package_name` must be specified.')

    engine = ProcessingEngine(
        input_files, package_name, id_label=id_label, noteid_label=noteid_label,
        notedate_label=notedate_label, notetext_label=notetext_label,
        noteorder_label=noteorder_label, metadata_labels=metadata_labels,
        concepts=concepts, **kwargs
    )

    with (
        open(outdir / 'bio_tag_data.csv', 'w', newline='') as out,
        open(outdir / 'bio_tag_data.jsonl', 'w') as jsonl,
    ):
        writer = csv.DictWriter(
            out,
            fieldnames=['index', 'studyid', 'note_id', 'domain', 'category', 'capture', 'start', 'end']
        )
        writer.writeheader()

        state = {'index': 0}

        def callback(studyid, note_id, note_date, text, metadata, concept, categories, matches):
            constant_meta = {
                'studyid': studyid,
                'note_id': note_id,
            }
            curr_note = {
                'note_id': note_id,
                'text': text,
                'results': [],
            }
            if matches:
                for category, m in zip(categories, matches):
                    label = get_result_label(category)
                    data = {
                        'index': state['index'],
                        'domain': concept.name,
                        'category': str(label),
                        'capture': m.group(),
                        'start': m.start(),
                        'end': m.end(),
                    }
                    writer.writerow(data | constant_meta)
                    curr_note['results'].append(data)
                    state['index'] += 1

            curr_note['results'] = sorted(curr_note['results'], key=lambda x: x['start'])
            jsonl.write(json.dumps(curr_note) + '\n')

        engine.run(callback)


if __name__ == '__main__':
    concept_cli(get_bio_tags)
