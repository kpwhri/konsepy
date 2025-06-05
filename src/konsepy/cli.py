import argparse
import datetime
from pathlib import Path

from konsepy.constants import NOTETEXT_LABEL, NOTEDATE_LABEL, NOTEID_LABEL, ID_LABEL


def concept_cli(func):
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    add_common_cli(parser)
    func(**clean_args(vars(parser.parse_args())))


def snippet_cli():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    parser.add_argument('--regexes', nargs='+',
                        help=r'REGEX_NAME==(?:re(?:gex)\sto\s(?:search|look)\sfor')
    parser.add_argument('--stop-after-regex-count', dest='stop_after_regex_count', default=None,
                        help='change to number if you want to limit number of regex "hits"; else keep None')
    parser.add_argument('--no-regex-func', dest='no_regex_func', action='store_true', default=False,
                        help='Run all regular expressions in `REGEXES` manaully, not calling `RUN_REGEX_FUNC`.')
    add_common_cli(parser)
    return clean_args(vars(parser.parse_args()))


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
                        help='Input CSV, JSONL, or SAS file(s) to read.')
    parser.add_argument('--encoding', type=str, default='latin1',
                        help='Encoding for input files. Output files will be utf8.')
    parser.add_argument('--id-label', default=ID_LABEL,
                        help='Column label for individual id')
    parser.add_argument('--noteid-label', default=NOTEID_LABEL,
                        help='Column label for note id')
    parser.add_argument('--notedate-label', default=NOTEDATE_LABEL,
                        help='Column label for date of note (optional)')
    parser.add_argument('--notetext-label', default=NOTETEXT_LABEL,
                        help='Column label for note text')
    parser.add_argument('--noteorder-label', default=None,
                        help='Specify column that enumerates the order of multiple parts of a single note. (optional)')
    parser.add_argument('--metadata-labels', default=None, nargs='*',
                        help='Specify additional column metadata as kwarg_name==in_dataset_name')
    parser.add_argument('--limit-noteids', default=None, nargs='+',
                        help='Limit run to only this noteid (useful for debugging).')
    return parser


def add_run_all_args(parser: argparse.ArgumentParser = None):
    if not parser:
        parser = argparse.ArgumentParser(fromfile_prefix_chars='@!')
    parser.add_argument('--incremental-output-only', action='store_true', default=False,
                        help='Do not retain summarized output, just output incremental jsonl file.')
    parser.add_argument('--concepts', nargs='+', default=False,
                        help='Look for these particular concepts.')


def _get_casting_func(target, format_=None):
    match target:
        case 'dt':
            if format_:
                return lambda x: datetime.datetime.strptime(x, format_)
            else:
                raise ValueError(f'Parsing datetime requires format string e.g., {target}==%m/%d/%y.'
                                 f' For info on formatting,'
                                 f' see https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior')
        case 'int':
            return lambda x: int(x)
        case 'float':
            return lambda x: float(x)
        case 'str':
            return lambda x: str(x)
    raise ValueError(f'Unrecognized cast request: {target}=={format_}')


def clean_metadata_labels(metadata_labels):
    result = {}
    for md_labels in metadata_labels:
        if '==' in md_labels:
            src, dest, *other = md_labels.split('==')
        else:
            src = md_labels
            dest = md_labels
            other = None
        func = _get_casting_func(*other) if other else lambda x: x
        result[src] = (dest, func)
    return result


def clean_args(args: dict):
    """Fix/format arguments, e.g., `metadata-labels`"""
    if args.get('metadata_labels', None):
        args['metadata_labels'] = clean_metadata_labels(args['metadata_labels'])
    return args


def parse_and_clean_args(parser: argparse.ArgumentParser) -> dict:
    """Wrapper to parse an clean arguments."""
    return clean_args(vars(parser.parse_args()))
