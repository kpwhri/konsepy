import argparse
from pathlib import Path

from konsepy.constants import NOTETEXT_LABEL, NOTEDATE_LABEL, NOTEID_LABEL, ID_LABEL


def concept_cli(func):
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    add_common_cli(parser)
    func(**vars(parser.parse_args()))


def snippet_cli():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    parser.add_argument('--regexes', nargs='+',
                        help=r'REGEX_NAME==(?:re(?:gex)\sto\s(?:search|look)\sfor')
    parser.add_argument('--stop-after-regex-count', dest='stop_after_regex_count', default=None,
                        help='change to number if you want to limit number of regex "hits"; else keep None')
    add_common_cli(parser)
    return vars(parser.parse_args())


def add_common_cli(parser: argparse.ArgumentParser):
    add_outdir_and_infiles(parser)
    parser.add_argument('--package-name', dest='package_name',
                        help='Name of package to run regular expressions from.')
    parser.add_argument('--concepts', nargs='+',
                        help='Name of concepts to process/run regular expressions for.')
    parser.add_argument('--require-regex', default=None,
                        help='Output text containing this regex but in which no regexes were found.')
    parser.add_argument('--start-after', default=0, type=int,
                        help='Start after skipping this many records')
    parser.add_argument('--stop-after', default=None, type=int,
                        help='change to number if you want to limit number of notes searched through; else None.')
    parser.add_argument('--select-probability', default=1.0, type=float,
                        help='Set to less than 1.0 to increase note sample (e.g., 0.3); 1.0=don\'t skip anything')
    parser.add_argument('--window-size', default=50, type=int,
                        help='Change the window for the pre/post contexts')


def add_outdir_and_infiles(parser: argparse.ArgumentParser = None):
    if not parser:
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    parser.add_argument('--outdir', type=Path, default=Path('.'),
                        help='Directory to place output files.')
    parser.add_argument('--input-files', nargs='+', type=str, default=list(),
                        help='Input CSV or SAS file(s) to read.')
    parser.add_argument('--id-label', default=ID_LABEL,
                        help='Column label for individual id')
    parser.add_argument('--noteid-label', default=NOTEID_LABEL,
                        help='Column label for note id')
    parser.add_argument('--notedate-label', default=NOTEDATE_LABEL,
                        help='Column label for date of note')
    parser.add_argument('--notetext-label', default=NOTETEXT_LABEL,
                        help='Column label for note text')
    parser.add_argument('--noteorder-label', default=None,
                        help='Specify column that enumerates the order of multiple parts of a single note.')
    return parser
