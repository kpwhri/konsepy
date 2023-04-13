"""
Simplify reading input files by creating an iterating wrapper.
"""
import csv
import random

from loguru import logger
from sas7bdat import SAS7BDAT

from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL


def iterate_csv_file(input_files, *, start_after=0, stop_after=None,
                     id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                     notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                     select_probability=1.0, encoding='latin1'):
    """Return count, mrn, note_id, text for each row in csv file"""
    count = 0
    total_count = 0
    for input_file in input_files:
        func = _extract_sas_file if input_file.endswith('sas7bdat') else _extract_csv_file
        for mrn, text, note_id, date in func(input_file, encoding, id_label, noteid_label, notedate_label,
                                             notetext_label):
            if random.random() > select_probability:
                continue
            total_count += 1
            if start_after >= total_count:
                continue
            count += 1
            yield count, mrn, note_id, date, text
            if stop_after and count > stop_after:
                return


def _extract_sas_file(input_file, encoding, id_label, noteid_label, notedate_label, notetext_label):
    with SAS7BDAT(input_file, skip_header=False, encoding=encoding) as fh:
        header = []
        for row in fh:
            if not header:
                header = row
                continue
            mrn = row[header.index(id_label)]
            date = row[header.index(notedate_label)] if notedate_label else ''
            text = row[header.index(noteid_label)]
            noteid = row[header.index(notetext_label)]
            yield mrn, text, noteid, date


def _extract_csv_file(input_file, encoding, id_label, noteid_label, notedate_label, notetext_label):
    with open(input_file, encoding=encoding) as fh:
        for row in csv.DictReader(fh):
            text = row[notetext_label]
            mrn = row[id_label]
            date = row.get(notedate_label, '')
            note_id = row[noteid_label]
            yield mrn, text, note_id, date


def output_results(outdir, *, not_found_text=None,
                   note_counter=None, cat_counter_mrns=None,
                   category_enums=None, note_to_cat=None, mrn_to_cat=None):
    categories = [e for category_enum in category_enums for e in category_enum]
    if not_found_text is not None:
        with open(outdir / 'snippets.csv', 'w', newline='') as out:
            writer = csv.writer(out)
            writer.writerow(['count', 'snippet'])
            for snippet, count in not_found_text.most_common():
                writer.writerow([count, ' '.join(snippet.split())])

    with open(outdir / 'category_counts.csv', 'w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['category', 'note_count', 'mrn_count'])
        for cat in categories:
            writer.writerow([cat, note_counter[cat], len(cat_counter_mrns[cat])])

    with open(outdir / 'mrn_category_counts.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn'] + categories)
        writer.writeheader()
        for mrn, note_counter in mrn_to_cat.items():
            writer.writerow({'mrn': mrn} | dict(note_counter))

    with open(outdir / 'notes_category_counts.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn', 'note_id'] + categories)
        writer.writeheader()
        for (mrn, note), note_counter in note_to_cat.items():
            writer.writerow({'mrn': mrn, 'note_id': note} | dict(note_counter))
    logger.info(f'Unique MRNs: {len(mrn_to_cat)}')
