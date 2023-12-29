import datetime
import json
from pathlib import Path

from loguru import logger

from konsepy.cli import add_outdir_and_infiles
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.textio import iterate_csv_file


def corpus2jsonl(input_files, outdir: Path, *,
                 id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                 notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                 noteorder_label=None, encoding='utf8',
                 ):
    """
    Convert a corpus to a jsonl format, suitable for using prodigy
    """
    dt = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(outdir / f'corpus_{dt}.jsonl', 'w', encoding='utf8') as out:
        for count, studyid, note_id, note_date, text in iterate_csv_file(
                input_files, encoding=encoding,
                id_label=id_label, noteid_label=noteid_label,
                notedate_label=notedate_label, notetext_label=notetext_label,
                noteorder_label=noteorder_label,
        ):
            out.write(json.dumps({
                'id': count,
                'studyid': studyid,
                'note_id': note_id,
                'note_date': note_date,
                'text': text,
            }) + '\n')
            if count % 10000 == 0:
                logger.info(f'Completed {count} records ({datetime.datetime.now()})')
    logger.info(f'DONE: Completed {count} records ({datetime.datetime.now()})')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    add_outdir_and_infiles(parser)
    corpus2jsonl(**vars(parser.parse_args()))
