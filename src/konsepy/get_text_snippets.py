import csv
import datetime
import re

from loguru import logger

from konsepy.cli import snippet_cli
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file


def get_text_snippets(input_files, outdir, regexes, *, start_after=0, stop_after=None, window_size=50,
                      id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                      notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                      select_probability=1.0, label='snippets', stop_after_regex_count=None):
    dt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    logger.warning('Snippets will have spaces normalized:'
                   ' multiple spaces/newlines/tabs will be converted'
                   ' to a single space in the output.')
    rx_count = 0
    outdir.mkdir(exist_ok=True)
    with open(outdir / f'{label}_{dt}.csv', 'w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['id', 'studyid', 'note_id', 'date', 'regex_name', 'precontext', 'term', 'postcontext'])
        for _, studyid, note_id, note_date, text in iterate_csv_file(
                input_files, start_after=start_after, stop_after=stop_after,
                id_label=id_label, noteid_label=noteid_label,
                notetext_label=notetext_label, notedate_label=notedate_label,
                select_probability=select_probability
        ):
            text = ' '.join(text.split())  # remove newlines, etc. (bad for snippets in Excel)
            for name, regex in regexes:
                if isinstance(regex, str):
                    regex = re.compile(regex, re.I)
                for m in regex.finditer(text):
                    precontext = text[max(m.start() - window_size, 0):m.start()]
                    postcontext = text[m.end():m.end() + window_size]
                    writer.writerow([
                        rx_count,  # id
                        studyid,
                        note_id,
                        note_date,
                        name,
                        precontext,
                        m.group(),  # term
                        postcontext,
                    ])
                    rx_count += 1
                    if stop_after_regex_count and rx_count >= stop_after_regex_count:
                        return


def get_text_snippets_for_concept_algorithm(package, input_files, outdir, *, concept_name=None, start_after=0,
                                            stop_after=None,
                                            window_size=50, regexes=None,
                                            id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                                            notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                                            select_probability=1.0, label='snippets', stop_after_regex_count=None,
                                            **kwargs):
    regexes = [(regex, category)
               for concept in get_all_concepts(package, concept_name)
               for regex, category in concept.regexes]

    get_text_snippets(input_files, outdir, regexes,
                      start_after=start_after,
                      stop_after=stop_after,
                      window_size=window_size,
                      select_probability=select_probability,
                      id_label=id_label,
                      noteid_label=noteid_label,
                      notedate_label=notedate_label,
                      notetext_label=notetext_label,
                      label=label,
                      stop_after_regex_count=stop_after_regex_count,
                      )


if __name__ == '__main__':
    kwargs = snippet_cli()
    kwargs['label'] = kwargs.get('concept_name', 'concept')

    if kwargs.get('concept_name', None):
        get_text_snippets_for_concept_algorithm(**kwargs)
    else:
        get_text_snippets(**kwargs)
