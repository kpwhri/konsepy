import datetime
import json
import pathlib
from collections import Counter, defaultdict

from loguru import logger

from konsepy.cli import add_outdir_and_infiles, add_run_all_args
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.importer import get_all_concepts
from konsepy.regex import extract_categories
from konsepy.textio import iterate_csv_file, output_results


def run_all(input_files, outdir: pathlib.Path, package_name: str, *,
            encoding='latin1', id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
            notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
            noteorder_label=None, incremental_output_only=False, concepts=None,
            include_text_output=False, **kwargs):
    logger.info(f'Arguments ignored: {kwargs}')
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    curr_outdir = outdir / f'run_all_{dt}'
    curr_outdir.mkdir(parents=True)
    logger.add(curr_outdir / f'run_all_{dt}.log')
    count = 0  # default value; received from forloop below
    cat_counter_notes = Counter()
    cat_counter_mrns = defaultdict(set)
    noteid_to_cat = defaultdict(Counter)
    mrn_to_cat = defaultdict(Counter)
    unique_mrns = set()
    concepts = list(get_all_concepts(package_name, *(concepts or list())))
    logger.info(f'Loaded {len(concepts)} concepts for processing.')
    with open(curr_outdir / 'output.jsonl', 'w') as out:
        for count, studyid, note_id, note_date, text in iterate_csv_file(
                input_files, encoding=encoding,
                id_label=id_label, noteid_label=noteid_label,
                notedate_label=notedate_label, notetext_label=notetext_label,
                noteorder_label=noteorder_label,
        ):
            if count % 10000 == 0:
                logger.info(f'Completed {count} records for {len(unique_mrns)} MRNs ({datetime.datetime.now()})')

            for concept in concepts:
                categories, matches = concept.run_func(text, include_match=True)
                if categories:
                    out.write(json.dumps({
                        'studyid': studyid,
                        'note_id': note_id,
                        'note_date': note_date,
                        'text': text if include_text_output else None,
                        'concept': concept.name,
                        'matches': matches,
                        'categories': categories,
                    }) + '\n')
                if not incremental_output_only:
                    extract_categories(
                        studyid, note_id, text, concept.run_func, categories=categories,
                        cat_counter_mrns=cat_counter_mrns, cat_counter_notes=cat_counter_notes,
                        mrn_to_cat=mrn_to_cat, noteid_to_cat=noteid_to_cat,
                        unique_mrns=unique_mrns
                    )
    logger.info(f'Finished. Total records: {count}  ({datetime.datetime.now()})')
    if not incremental_output_only:
        output_results(curr_outdir, note_counter=cat_counter_notes,
                       cat_counter_mrns=cat_counter_mrns,
                       category_enums=[c.category_enum for c in concepts],
                       note_to_cat=noteid_to_cat, mrn_to_cat=mrn_to_cat)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    add_outdir_and_infiles(parser)
    add_run_all_args(parser)
    run_all(**vars(parser.parse_args()))
