import datetime
import re
from collections import Counter, defaultdict

from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.context.contexts import get_contexts
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file, output_results
from loguru import logger

from konsepy.engine import ProcessingEngine


def run_regex_on_files(input_files, regex_func, package_name=None, *, start_after=0, stop_after=None,
                       require_regex=None, window_size=50,
                       id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                       notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                       noteorder_label=None, metadata_labels=None,
                       select_probability=1.0, **kwargs):
    cat_counter_notes = Counter()
    cat_counter_mrns = defaultdict(set)
    noteid_to_cat = defaultdict(Counter)
    mrn_to_cat = defaultdict(Counter)
    unique_mrns = set()
    not_found_text = Counter()
    if require_regex:
        require_regex = re.compile(require_regex, re.I)

    for count, mrn, note_id, note_date, text, metadata in iterate_csv_file(
            input_files, start_after=start_after, stop_after=stop_after,
            id_label=id_label, noteid_label=noteid_label,
            notedate_label=notedate_label, notetext_label=notetext_label,
            noteorder_label=noteorder_label, metadata_labels=metadata_labels,
            select_probability=select_probability,
    ):
        if count % 50000 == 0:
            logger.info(
                f'Completed {count:,} records:'
                f' {len(unique_mrns):,} MRNs contain any category ({datetime.datetime.now()})')
        extract_categories(
            mrn, note_id, text, regex_func,
            cat_counter_mrns=cat_counter_mrns, cat_counter_notes=cat_counter_notes,
            mrn_to_cat=mrn_to_cat, require_regex=require_regex,
            not_found_text=not_found_text, noteid_to_cat=noteid_to_cat,
            unique_mrns=unique_mrns, window_size=window_size
        )
    logger.info(f'Finished. Total records: {count:,}  ({datetime.datetime.now()})')
    return cat_counter_notes, cat_counter_mrns, not_found_text, mrn_to_cat, noteid_to_cat


def extract_categories(mrn, note_id, text, regex_func, *, categories=None,
                       cat_counter_mrns=None, cat_counter_notes=None, mrn_to_cat=None,
                       not_found_text=None, noteid_to_cat=None,
                       require_regex=None, unique_mrns=None, window_size=50):
    if categories is None:  # don't re-run when empty list
        categories = list(regex_func(text, categories_only=True))
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
                         notedate_label=NOTETEXT_LABEL, notetext_label=NOTETEXT_LABEL,
                         noteorder_label=None, select_probability=1.0, **kwargs):
    logger.info(f'Arguments ignored: {kwargs}')
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Use ProcessingEngine to consolidate concept loading and iteration
    engine = ProcessingEngine(
        input_files, package_name, start_after=start_after, stop_after=stop_after,
        id_label=id_label, noteid_label=noteid_label,
        notedate_label=notedate_label, notetext_label=notetext_label,
        noteorder_label=noteorder_label, select_probability=select_probability,
        concepts=concepts, **kwargs
    )

    # Note: the original run_regex_and_output created a separate output directory
    # PER CONCEPT. This is a bit different from run_all.
    # To maintain backward compatibility, we'll keep that behavior.

    for iconcept in engine.concepts:
        curr_outdir = outdir / f'{iconcept.name}_{dt}'
        curr_outdir.mkdir(parents=True)
        logger.add(curr_outdir / f'{iconcept.name}_{dt}.log')

        note_counter, cat_counter_mrns, not_found_text, mrn_to_cat, note_to_cat = run_regex_on_files(
            input_files, iconcept.run_func, package_name=package_name,
            start_after=start_after, stop_after=stop_after, require_regex=require_regex,
            window_size=window_size,
            id_label=id_label, noteid_label=noteid_label,
            notedate_label=notedate_label, notetext_label=notetext_label,
            noteorder_label=noteorder_label, select_probability=select_probability,
            **kwargs
        )
        output_results(curr_outdir, not_found_text=not_found_text, note_counter=note_counter,
                       cat_counter_mrns=cat_counter_mrns, category_enums=iconcept.category_enums,
                       note_to_cat=note_to_cat, mrn_to_cat=mrn_to_cat)
