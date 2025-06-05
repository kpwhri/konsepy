import datetime
import json
import pathlib

from loguru import logger

from konsepy.cli import add_outdir_and_infiles, add_run_all_args, clean_args
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file


def run4snippets(input_files, outdir: pathlib.Path, package_name: str, *,
                 context_length=180, max_window=500,
                 encoding='utf8', id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                 notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                 noteorder_label=None, metadata_labels=None,
                 concepts=None, limit_noteids=None, **kwargs) -> pathlib.Path:
    """
    Run all concepts.
    Return: Newly created `run_all` directory.
    """
    logger.info(f'Arguments ignored: {kwargs}')
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    curr_outdir = outdir / f'run_all_{dt}'
    curr_outdir.mkdir(parents=True)
    logger.add(curr_outdir / f'run_all_{dt}.log')
    count = 0  # default value; received from forloop below
    unique_mrns = set()
    concepts = list(get_all_concepts(package_name, *(concepts or list())))
    logger.info(f'Loaded {len(concepts)} concepts for processing.')
    with open(curr_outdir / 'output.jsonl', 'w') as out:
        for count, studyid, note_id, note_date, text, metadata in iterate_csv_file(
                input_files, encoding=encoding,
                id_label=id_label, noteid_label=noteid_label,
                notedate_label=notedate_label, notetext_label=notetext_label,
                noteorder_label=noteorder_label, metadata_labels=metadata_labels,
        ):
            if limit_noteids and note_id not in limit_noteids:
                continue
            if count % 50000 == 0:
                logger.info(f'Completed {count:,} records:'
                            f' {len(unique_mrns):,} MRNs contain any category ({datetime.datetime.now()})')

            for concept in concepts:
                categories, matches = concept.run_func(text, include_match=True, **metadata)
                for m, category in zip(matches, categories):
                    out.write(json.dumps({
                        # keep order: first three will display in textual_review_app
                        'note_id': note_id,
                        'concept': concept.name,
                        'category': category,
                        'studyid': studyid,
                        'note_date': note_date,
                        'match': m.group(),
                        'start_index': m.start(),
                        'end_index': m.end(),
                        'precontext': text[max(m.start() - context_length, 0): m.start()],
                        'postcontext': text[m.end(): m.end() + context_length],
                        'pretext': text[max(m.start() - max_window, 0): m.start()],  # TODO: configure how much to show
                        'posttext': text[m.end(): m.end() + max_window],  # TODO: configure how much to show
                    }) + '\n')

    logger.info(f'Finished. Total records: {count:,}  ({datetime.datetime.now()})')
    return curr_outdir


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    add_outdir_and_infiles(parser)
    add_run_all_args(parser)
    parser.add_argument('--context-length', 'context_length', type=int, default=180,
                        help='Default context window to show around match.')
    parser.add_argument('--max-window', 'max_window', type=int, default=500,
                        help='Maximum context window that will be output and available for review.')
    run4snippets(**clean_args(vars(parser.parse_args())))
