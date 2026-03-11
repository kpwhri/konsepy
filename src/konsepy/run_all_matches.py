import datetime
import json
import pathlib
from loguru import logger

from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.context.contexts import get_contexts
from konsepy.engine import ProcessingEngine


def run_all_matches(input_files, outdir: pathlib.Path, package_name: str, *,
                    encoding='latin1', id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                    notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                    noteorder_label=None, metadata_labels=None,
                    concepts=None, limit_noteids=None, window=30, word_window=None, **kwargs) -> pathlib.Path:
    """
    Run all concepts and output each match as a separate JSONL row.
    Return: Newly created `run_all_matches` directory.
    """
    if kwargs:
        logger.info(f'Arguments ignored: {kwargs}')
    dt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    curr_outdir = outdir / f'run_all_matches_{dt}'
    curr_outdir.mkdir(parents=True)
    logger.add(curr_outdir / f'run_all_matches_{dt}.log')

    engine = ProcessingEngine(
        input_files, package_name, encoding=encoding, id_label=id_label,
        noteid_label=noteid_label, notedate_label=notedate_label,
        notetext_label=notetext_label, noteorder_label=noteorder_label,
        metadata_labels=metadata_labels, concepts=concepts,
        limit_noteids=limit_noteids, **kwargs
    )

    output_path = curr_outdir / 'output.jsonl'
    with open(output_path, 'w', encoding='utf8') as out:
        def callback(studyid, note_id, note_date, text, metadata, concept, categories, matches):
            if not matches:
                return

            for category, m in zip(categories, matches):
                # serialize category cleanly
                cat_name = category.name if hasattr(category, 'name') else str(category)

                contexts = get_contexts(m, text, window=window, word_window=word_window)
                row = {
                    'studyid': studyid,
                    'note_id': note_id,
                    'note_date': note_date,
                    'concept': concept.name,
                    'category': cat_name,
                    'precontext': contexts['precontext'],
                    'match': m.group(),
                    'postcontext': contexts['postcontext'],
                    'start_index': m.start(),
                    'end_index': m.end(),
                }
                if metadata:
                    row.update(metadata)
                if group_dict := m.groupdict():
                    row.update(group_dict)

                out.write(json.dumps(row) + '\n')

        engine.run(callback)

    return curr_outdir
