import argparse
import sys
from pathlib import Path
from loguru import logger

from konsepy.run_all import run_all
from konsepy.run4snippets import run4snippets
from konsepy.bio_tag import get_bio_tags
from konsepy.corpus2jsonl import corpus2jsonl
from konsepy.create_bio_dataset import create_bio_dataset
from konsepy.cli import add_outdir_and_infiles, add_run_all_args, clean_args, clean_metadata_labels


def main():
    parser = argparse.ArgumentParser(description='konsepy: NLP information extraction using regular expressions')
    subparsers = parser.add_subparsers(dest='command', help='Sub-commands')

    # run-all
    run_all_parser = subparsers.add_parser('run-all', help='Run all concepts')
    add_outdir_and_infiles(run_all_parser)
    add_run_all_args(run_all_parser)
    run_all_parser.add_argument('--package-name', required=True,
                                help='Name of package to run regular expressions from.')
    run_all_parser.add_argument('--include-text-output', action='store_true',
                                help='Include original text in output jsonl.')

    # run4snippets
    run4snippets_parser = subparsers.add_parser('run4snippets', help='Extract snippets for review')
    add_outdir_and_infiles(run4snippets_parser)
    add_run_all_args(run4snippets_parser)
    run4snippets_parser.add_argument('--package-name', required=True,
                                     help='Name of package to run regular expressions from.')
    run4snippets_parser.add_argument('--context-length', type=int, default=180,
                                     help='Default context window.')
    run4snippets_parser.add_argument('--max-window', type=int, default=500,
                                     help='Maximum context window.')
    run4snippets_parser.add_argument('--target-concepts', nargs='+',
                                     help='Target concepts.')
    run4snippets_parser.add_argument('--target-categories', nargs='+',
                                     help='Target categories.')
    run4snippets_parser.add_argument('--order-metadata', nargs='+',
                                     help='Specify first metadata items in output.')

    # bio-tag
    bio_tag_parser = subparsers.add_parser('bio-tag', help='Generate BIO tagged data')
    add_outdir_and_infiles(bio_tag_parser)
    bio_tag_parser.add_argument('--package-name', required=True, help='Name of package.')

    # corpus2jsonl
    corpus2jsonl_parser = subparsers.add_parser('corpus2jsonl', help='Convert corpus to jsonl')
    add_outdir_and_infiles(corpus2jsonl_parser)
    corpus2jsonl_parser.add_argument('--split', choices=['sentence', 'chunk', 'window'], help='Split type')
    corpus2jsonl_parser.add_argument('--max-seq-length', dest='max_seq_length', default=512, type=int,
                                     help='Number of tokens to retain when `--split` is sent_chunk or sent_window.')
    corpus2jsonl_parser.add_argument('--tokenizer', default=None,
                                     help='Path to BERT tokenizer.')

    # create-bio-dataset
    create_bio_ds_parser = subparsers.add_parser('create-bio-dataset', help='Create BIO dataset for training')
    create_bio_ds_parser.add_argument('path', type=Path, help='Path to jsonl input file.')
    create_bio_ds_parser.add_argument('outpath', type=Path, help='Path to write created dataset.')
    create_bio_ds_parser.add_argument('--test-size', type=float, default=0.1)
    create_bio_ds_parser.add_argument('--validation-size', type=float, default=0.05)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    cmd_args = vars(args)
    command = cmd_args.pop('command')

    # clean args (e.g. metadata_labels)
    cmd_args = clean_args(cmd_args)

    if command == 'run-all':
        run_all(**cmd_args)
    elif command == 'run4snippets':
        run4snippets(**cmd_args)
    elif command == 'bio-tag':
        get_bio_tags(**cmd_args)
    elif command == 'corpus2jsonl':
        corpus2jsonl(**cmd_args)
    elif command == 'create-bio-dataset':
        create_bio_dataset(**cmd_args)


if __name__ == '__main__':
    main()
