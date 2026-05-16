"""
Simplify reading input files by creating an iterating wrapper.
"""
import csv
import json
import random
import sqlite3
from collections import defaultdict
from pathlib import Path

from loguru import logger

from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL


class DictReaderInsensitive(csv.DictReader):
    """
    Overrides the csv.fieldnames property making fieldnames stripped and lowercase
    Based on: https://stackoverflow.com/a/16937568/1165522
    """

    @property
    def fieldnames(self):
        fnames = csv.DictReader.fieldnames.fget(self)
        if fnames is None:
            return None
        return [field.strip().lower() for field in fnames]


def iterate_csv_file(input_files, *, start_after=0, stop_after=None,
                     id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                     notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                     noteorder_label=None, metadata_labels=None,
                     select_probability=1.0, encoding='latin1'):
    """
    Return count, mrn, note_id, text for each row in csv file

    count: auto-incremented for each record
    """
    count = 0
    total_count = 0
    for input_file in input_files:
        func = None
        if not isinstance(input_file, Path):
            input_file = Path(input_file)
        match input_file.suffix:
            case '.sas7bdat':
                func = _extract_sas_file
            case '.csv':
                func = _extract_csv_file
            case '.tsv':
                func = _extract_csv_file
            case '.jsonl':
                func = _extract_jsonl_file
            case '.db':
                func = _extract_sqlite_file
            case '.sqlite':
                func = _extract_sqlite_file
            case _:
                logger.warning(f'Failed to read corpus file (`input_file`): {input_file}')
                continue
        for mrn, text, note_id, date, md in _deline_lines(
                func, input_file, encoding, id_label, noteid_label,
                notedate_label, notetext_label, noteorder_label,
                metadata_labels):
            if select_probability < 1.0 and random.random() > select_probability:
                continue
            total_count += 1
            if start_after >= total_count:
                continue
            count += 1
            yield count, mrn, note_id, date, text, md
            if stop_after and count > stop_after:
                return


def _deline_lines(func, input_file, encoding, mrn_label, noteid_label,
                  notedate_label, notetext_label, noteorder_label=None,
                  metadata_labels=None):
    # variables for delining notes
    curr_id = None
    curr_mrn = None
    curr_date = None
    curr_doc = []
    for mrn, text, note_id, date, order, md in func(
            input_file, encoding, mrn_label, noteid_label, notedate_label,
            notetext_label, noteorder_label, metadata_labels,
    ):
        if not order:  # skip delining
            yield mrn, text, note_id, date, md
        else:
            if curr_id is None:
                curr_id = note_id
                curr_mrn = mrn
                curr_date = date
            elif note_id != curr_id:
                yield curr_mrn, ' '.join(text for _, _, text in sorted(curr_doc)), curr_id, curr_date, md
                curr_id = note_id
                curr_mrn = mrn
                curr_date = date
                curr_doc = []
            if isinstance(text, float) or not text:
                continue  # skip empty text
            curr_doc.append((note_id, order, text))  # keep track of all text associated with this note
    if curr_id is not None:
        yield curr_mrn, ' '.join(text for _, _, text in sorted(curr_doc)), curr_id, curr_date, md


def _extract_sas_file(input_file, encoding, id_label, noteid_label,
                      notedate_label, notetext_label, noteorder_label=None,
                      metadata_labels=None):
    from sas7bdat import SAS7BDAT
    with SAS7BDAT(input_file, skip_header=False, encoding=encoding) as fh:
        header = []
        for row in fh:
            if not header:
                header = row
                continue
            mrn = row[header.index(id_label)]
            date = row[header.index(notedate_label)] if notedate_label and notedate_label in header else ''
            noteid = row[header.index(noteid_label)]
            text = row[header.index(notetext_label)]
            order = row[header.index(noteorder_label)] if noteorder_label and noteorder_label in header else None
            metadata = {}
            if metadata_labels:
                for src, (dest, func) in metadata_labels.items():
                    metadata[dest] = func(row[header.index(src)])
            yield mrn, text, noteid, date, order, metadata


def _extract_csv_file(input_file, encoding, id_label, noteid_label, notedate_label,
                      notetext_label, noteorder_label=None, metadata_labels=None):
    with open(input_file, newline='', encoding=encoding) as fh:
        for row in DictReaderInsensitive(fh):
            text = row[notetext_label]
            mrn = row[id_label]
            date = row.get(notedate_label, '')
            note_id = row[noteid_label]
            order = row.get(noteorder_label, '')
            metadata = {}
            if metadata_labels:
                for src, (dest, func) in metadata_labels.items():
                    metadata[dest] = func(row[src])
            yield mrn, text, note_id, date, order, metadata


def _extract_jsonl_file(input_file, encoding, id_label, noteid_label, notedate_label,
                        notetext_label, noteorder_label=None, metadata_labels=None):
    with open(input_file, encoding=encoding) as fh:
        for line in fh:
            data = json.loads(line.strip())
            text = data[notetext_label]
            mrn = data[id_label]
            date = data.get(notedate_label, '')
            note_id = data[noteid_label]
            order = data.get(noteorder_label, '')
            metadata = {}
            if metadata_labels:
                for src, (dest, func) in metadata_labels.items():
                    metadata[dest] = func(data[src])
            yield mrn, text, note_id, date, order, metadata


def _extract_sqlite_file(input_file, encoding, id_label, noteid_label, notedate_label,
                         notetext_label, noteorder_label=None, metadata_labels=None,
                         tablename='notes'):
    with sqlite3.connect(input_file) as connection:
        connection.row_factory = sqlite3.Row

        columns = [id_label, noteid_label, notetext_label]
        if notedate_label:
            columns.append(notedate_label)
        if noteorder_label:
            columns.append(noteorder_label)
        if metadata_labels:
            columns.extend(metadata_labels.keys())

        column_sql = ', '.join(f'"{column}"' for column in columns)
        query = f'SELECT {column_sql} FROM "{tablename}"'

        for row in connection.execute(query):
            text = row[notetext_label]
            mrn = row[id_label]
            date = row[notedate_label] if notedate_label and notedate_label in row.keys() else ''
            note_id = row[noteid_label]
            order = row[noteorder_label] if noteorder_label and noteorder_label in row.keys() else ''
            metadata = {}
            if metadata_labels:
                for src, (dest, func) in metadata_labels.items():
                    metadata[dest] = func(row[src])
            yield mrn, text, note_id, date, order, metadata


def output_results(outdir, *, not_found_text=None,
                   note_counter=None, cat_counter_mrns=None,
                   category_enums=None, note_to_cat=None, mrn_to_cat=None,
                   extraction_rows=None):
    categories = [e for category_enum in category_enums for e in category_enum]
    category_names = [str(e) for e in categories]
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
            writer.writerow(
                [
                    str(cat),
                    _get_counter_value(note_counter, cat),
                    _get_counter_set_size(cat_counter_mrns, cat),
                ]
            )

    with open(outdir / 'mrn_category_counts.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn'] + category_names)
        writer.writeheader()
        for mrn, note_counter in mrn_to_cat.items():
            writer.writerow({'mrn': mrn} | _stringify_counter(note_counter))

    with open(outdir / 'notes_category_counts.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn', 'note_id'] + category_names)
        writer.writeheader()
        for (mrn, note), note_counter in note_to_cat.items():
            writer.writerow({'mrn': mrn, 'note_id': note} | _stringify_counter(note_counter))
    if extraction_rows:
        output_extraction_results(outdir, extraction_rows)
    logger.info(f'Unique MRNs with any category: {len(mrn_to_cat):,}')


def output_extraction_results(outdir, extraction_rows):
    """Write extraction-specific output files."""
    _output_extracted_values(outdir, extraction_rows)
    _output_extracted_max_per_note(outdir, extraction_rows)
    _output_extracted_max_per_mrn(outdir, extraction_rows)
    _output_extracted_sum_of_group_maxima(outdir, extraction_rows)


def _output_extracted_values(outdir, extraction_rows):
    with open(outdir / 'extracted_values.csv', 'w', newline='') as out:
        fieldnames = ['mrn', 'note_id', 'category', 'value', 'group']
        writer = csv.DictWriter(out, fieldnames)
        writer.writeheader()
        writer.writerows(extraction_rows)


def _output_extracted_max_per_note(outdir, extraction_rows):
    max_by_note = {}

    for row in extraction_rows:
        value = _coerce_number(row['value'])
        if value is None:
            continue

        key = (row['mrn'], row['note_id'], row['category'])
        if key not in max_by_note or value > max_by_note[key]:
            max_by_note[key] = value

    with open(outdir / 'extracted_max_per_note.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn', 'note_id', 'category', 'max_value'])
        writer.writeheader()

        for (mrn, note_id, category), max_value in sorted(max_by_note.items()):
            writer.writerow(
                {
                    'mrn': mrn,
                    'note_id': note_id,
                    'category': category,
                    'max_value': max_value,
                }
            )


def _output_extracted_max_per_mrn(outdir, extraction_rows):
    max_by_mrn = {}

    for row in extraction_rows:
        value = _coerce_number(row['value'])
        if value is None:
            continue

        key = (row['mrn'], row['category'])
        if key not in max_by_mrn or value > max_by_mrn[key]:
            max_by_mrn[key] = value

    with open(outdir / 'extracted_max_per_mrn.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn', 'category', 'max_value'])
        writer.writeheader()

        for (mrn, category), max_value in sorted(max_by_mrn.items()):
            writer.writerow(
                {
                    'mrn': mrn,
                    'category': category,
                    'max_value': max_value,
                }
            )


def _output_extracted_sum_of_group_maxima(outdir, extraction_rows):
    max_by_group = {}

    for row in extraction_rows:
        value = _coerce_number(row['value'])
        group = row.get('group')

        if value is None or group is None:
            continue

        key = (row['mrn'], row['category'], group)
        if key not in max_by_group or value > max_by_group[key]:
            max_by_group[key] = value

    sum_by_mrn = defaultdict(int)

    for (mrn, category, _group), max_value in max_by_group.items():
        sum_by_mrn[(mrn, category)] += max_value

    with open(outdir / 'extracted_sum_of_group_maxima.csv', 'w', newline='') as out:
        writer = csv.DictWriter(out, ['mrn', 'category', 'sum_of_group_maxima'])
        writer.writeheader()

        for (mrn, category), total in sorted(sum_by_mrn.items()):
            writer.writerow(
                {
                    'mrn': mrn,
                    'category': category,
                    'sum_of_group_maxima': total,
                }
            )


def _coerce_number(value):
    if isinstance(value, (int, float)):
        return value

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _stringify_counter(counter):
    return {str(key): value for key, value in counter.items()}


def _get_counter_value(counter, key):
    if key in counter:
        return counter[key]
    key_name = str(key)
    return counter.get(key_name, 0)


def _get_counter_set_size(counter, key):
    if key in counter:
        return len(counter[key])
    key_name = str(key)
    return len(counter.get(key_name, set()))
