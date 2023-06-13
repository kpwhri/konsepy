import datetime
import re
from collections import Counter, defaultdict

from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file, output_results
from loguru import logger


def run_regex_on_files(input_files, regex_func, *, start_after=0, stop_after=None,
                       require_regex=None, window_size=50,
                       id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                       notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                       noteorder_label=None, select_probability=1.0):
    count = 0  # default value; received from forloop below
    cat_counter_notes = Counter()
    cat_counter_mrns = defaultdict(set)
    noteid_to_cat = defaultdict(Counter)
    mrn_to_cat = defaultdict(Counter)
    unique_mrns = set()
    not_found_text = Counter()
    if require_regex:
        require_regex = re.compile(require_regex, re.I)
    for count, mrn, note_id, note_date, text in iterate_csv_file(
            input_files, start_after=start_after, stop_after=stop_after,
            id_label=id_label, noteid_label=noteid_label,
            notedate_label=notedate_label, notetext_label=notetext_label,
            noteorder_label=noteorder_label, select_probability=select_probability,
    ):
        if count % 10000 == 0:
            logger.info(
                f'Completed {count} records: {len(unique_mrns)} MRNs contain any category ({datetime.datetime.now()})')
        extract_categories(
            mrn, note_id, text, regex_func,
            cat_counter_mrns=cat_counter_mrns, cat_counter_notes=cat_counter_notes,
            mrn_to_cat=mrn_to_cat, require_regex=require_regex,
            not_found_text=not_found_text, noteid_to_cat=noteid_to_cat,
            unique_mrns=unique_mrns, window_size=window_size
        )
    logger.info(f'Finished. Total records: {count}  ({datetime.datetime.now()})')
    return cat_counter_notes, cat_counter_mrns, not_found_text, mrn_to_cat, noteid_to_cat


def extract_categories(mrn, note_id, text, regex_func, *,
                       cat_counter_mrns=None, cat_counter_notes=None, mrn_to_cat=None,
                       not_found_text=None, noteid_to_cat=None,
                       require_regex=None, unique_mrns=None, window_size=50):
    categories = list(regex_func(text))
    for category in categories:
        mrn_to_cat[mrn][category] += 1
        noteid_to_cat[(mrn, note_id)][category] += 1
        cat_counter_notes[category] += 1
        cat_counter_mrns[category].add(mrn)
    if categories:
        unique_mrns.add(mrn)
    if not categories and not_found_text:
        if require_regex:
            for m in require_regex.finditer(text):
                start_snippet = max(0, m.start() - window_size)
                end_snippet = m.end() + window_size
                snippet = text[start_snippet:end_snippet + 1]
                not_found_text[' '.join(snippet.split())] += 1
        else:
            not_found_text[' '.join(text.split())] += 1


def run_regex_and_output(package_name, input_files, outdir, *concepts,
                         start_after=0, stop_after=None, require_regex=None, window_size=50,
                         id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                         notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                         noteorder_label=None, select_probability=1.0):
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    for iconcept in get_all_concepts(package_name, *concepts):
        curr_outdir = outdir / f'{iconcept.name}_{dt}'
        curr_outdir.mkdir(parents=True)
        logger.add(curr_outdir / f'{iconcept.name}_{dt}.log')
        note_counter, cat_counter_mrns, not_found_text, mrn_to_cat, note_to_cat = run_regex_on_files(
            input_files, iconcept.run_func,
            start_after=start_after, stop_after=stop_after, require_regex=require_regex,
            window_size=window_size,
            id_label=id_label, noteid_label=noteid_label,
            notedate_label=notedate_label, notetext_label=notetext_label,
            noteorder_label=noteorder_label, select_probability=select_probability,
        )
        output_results(curr_outdir, not_found_text=not_found_text, note_counter=note_counter,
                       cat_counter_mrns=cat_counter_mrns, category_enums=[iconcept.category_enum],
                       note_to_cat=note_to_cat, mrn_to_cat=mrn_to_cat)


def search_first_regex(regexes):
    """For each regex, only return first instance (use search)"""

    def _search_first_regex(text):
        for regex, category in regexes:
            if regex.search(text):
                yield category

    return _search_first_regex


def search_all_regex(regexes):
    """For each regex, return all (use finditer)"""

    def _search_all_regex(text):
        for regex, category in regexes:
            for _ in regex.finditer(text):
                yield category

    return _search_all_regex


def get_all_regex_by_index(regexes):
    """For each regex, return all results, including indices"""

    def _get_all_regex_by_index(text):
        for regex, category in regexes:
            for m in regex.finditer(text):
                yield category.name, m.group(), m.start(), m.end()

    return _get_all_regex_by_index
