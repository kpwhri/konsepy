import csv
import datetime
import itertools
import re

from loguru import logger

from konsepy.cli import snippet_cli
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file


def get_text_snippets_regexes(input_files, outdir, regexes, *, start_after=0, stop_after=None, window_size=50,
                              encoding='latin1', id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                              notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                              noteorder_label=None, metadata_labels=None,
                              select_probability=1.0, label='snippets', stop_after_regex_count=None, **kwargs):
    dt = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    logger.warning('Snippets will have spaces normalized:'
                   ' multiple spaces/newlines/tabs will be converted'
                   ' to a single space in the output.')
    rx_count = 0
    outdir.mkdir(exist_ok=True)
    outfile = outdir / f'{label}_{dt}.csv'
    with open(outfile, 'w', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(['id', 'studyid', 'note_id', 'date', 'regex_name', 'precontext', 'term', 'postcontext'])
        for i, (_, studyid, note_id, note_date, text, metadata) in enumerate(iterate_csv_file(
                input_files, encoding=encoding,
                start_after=start_after, stop_after=stop_after,
                id_label=id_label, noteid_label=noteid_label,
                notetext_label=notetext_label, notedate_label=notedate_label,
                noteorder_label=noteorder_label, metadata_labels=metadata_labels,
                select_probability=select_probability,
        ), start=1):
            text = ' '.join(text.split())  # remove newlines, etc. (bad for snippets in Excel)
            for regex_ in regexes:
                if isinstance(regex_, (str, tuple)):
                    if isinstance(regex_, str):
                        name, regex = regex_.split('==')
                    elif isinstance(regex_, tuple):
                        name, regex = regex_
                    if isinstance(regex, str):
                        regex = re.compile(regex, re.I)
                    func = lambda x: zip(itertools.repeat(name), regex.finditer(x))
                elif callable(regex_):
                    func = lambda x: regex_(x, include_match=True, **metadata)
                else:
                    raise ValueError(f'Unknown how to handle regular expression of type {type(regex_)}: {regex_}')
                for name, m in zip(func(text)):
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
            if i % 1000 == 0:
                logger.info(f'Completed {i} records, found {rx_count} matches.')
    return outfile


def get_text_snippets_for_concept_algorithm(package_name, input_files, outdir, *, concepts=None,
                                            encoding='latin1',
                                            start_after=0, stop_after=None, window_size=50,
                                            id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                                            notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                                            noteorder_label=None,
                                            select_probability=1.0, label='snippets', stop_after_regex_count=None,
                                            no_regex_func=False,
                                            **kwargs):
    if concepts is None:
        concepts = list()
    if no_regex_func:  # ignore negation, add functions, the RUN_REGEX_FUNC
        regexes = [(category, regex)
                   for concept in get_all_concepts(package_name, *concepts)
                   for regex, category, *_ in concept.regexes]
    else:
        regexes = [concept.run_func for concept in get_all_concepts(package_name, *concepts)]

    return get_text_snippets_regexes(input_files, outdir, regexes,
                                     encoding=encoding,
                                     start_after=start_after,
                                     stop_after=stop_after,
                                     window_size=window_size,
                                     select_probability=select_probability,
                                     id_label=id_label,
                                     noteid_label=noteid_label,
                                     notedate_label=notedate_label,
                                     notetext_label=notetext_label,
                                     noteorder_label=noteorder_label,
                                     label=label,
                                     stop_after_regex_count=stop_after_regex_count,
                                     )


def get_text_snippets_cli(package_name=None):
    kwargs = snippet_cli()
    kwargs['package_name'] = kwargs.get('package_name', package_name) or package_name

    if package_name and kwargs.get('regexes', None) is None:
        return get_text_snippets_for_concept_algorithm(**kwargs)
    else:
        return get_text_snippets_regexes(**kwargs)


if __name__ == '__main__':
    get_text_snippets_cli()
