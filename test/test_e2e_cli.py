import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from konsepy.main import main


try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

try:
    import datasets
    HAS_DATASETS = True
except ImportError:
    HAS_DATASETS = False


@pytest.fixture
def input_file(request):
    return Path(request.fspath).parent / 'data' / 'corpus.jsonl'


def test_cli_run_all(tmp_path, input_file):
    outdir = tmp_path / 'run_all_out'
    outdir.mkdir()

    test_args = [
        'konsepy',
        'run-all',
        '--input-files', str(input_file),
        '--outdir', str(outdir),
        '--package-name', 'example_nlp',
        '--id-label', 'chapter',
        '--noteid-label', 'chapter',
    ]

    with patch.object(sys, 'argv', test_args):
        main()

    # verify that an output directory was created (it has a timestamp)
    run_all_dirs = list(outdir.glob('run_all_*'))
    assert len(run_all_dirs) == 1
    actual_outdir = run_all_dirs[0]

    assert (actual_outdir / 'output.jsonl').exists()
    assert (actual_outdir / 'category_counts.csv').exists()

    with open(actual_outdir / 'output.jsonl', encoding='utf8') as f:
        lines = f.readlines()
        assert len(lines) > 0
        first_entry = json.loads(lines[0])
        assert 'concept' in first_entry
        assert 'categories' in first_entry


def test_cli_run4snippets(tmp_path, input_file):
    outdir = tmp_path / 'snippets_out'
    outdir.mkdir()

    test_args = [
        'konsepy',
        'run4snippets',
        '--input-files', str(input_file),
        '--outdir', str(outdir),
        '--package-name', 'example_nlp',
        '--id-label', 'chapter',
        '--noteid-label', 'chapter',
    ]

    with patch.object(sys, 'argv', test_args):
        main()

    snippet_dirs = list(outdir.glob('run_all_*'))
    assert len(snippet_dirs) == 1
    actual_outdir = snippet_dirs[0]

    assert (actual_outdir / 'output.jsonl').exists()
    with open(actual_outdir / 'output.jsonl', encoding='utf8') as f:
        lines = f.readlines()
        assert len(lines) > 0
        first_entry = json.loads(lines[0])
        assert 'precontext' in first_entry
        assert 'postcontext' in first_entry
        assert 'match' in first_entry


def test_cli_bio_tag(tmp_path, input_file):
    outdir = tmp_path / 'bio_tag_out'
    outdir.mkdir()

    test_args = [
        'konsepy',
        'bio-tag',
        '--input-files', str(input_file),
        '--outdir', str(outdir),
        '--package-name', 'example_nlp',
        '--id-label', 'chapter',
        '--noteid-label', 'chapter',
    ]

    with patch.object(sys, 'argv', test_args):
        main()

    assert (outdir / 'bio_tag_data.csv').exists()
    assert (outdir / 'bio_tag_data.jsonl').exists()


@pytest.mark.skipif(not HAS_SPACY, reason='spacy not installed')
def test_cli_corpus2jsonl(tmp_path, input_file):
    outdir = tmp_path / 'corpus2jsonl_out'
    outdir.mkdir()

    test_args = [
        'konsepy',
        'corpus2jsonl',
        '--input-files', str(input_file),
        '--outdir', str(outdir),
        '--id-label', 'chapter',
        '--noteid-label', 'chapter',
    ]

    with patch.object(sys, 'argv', test_args):
        main()

    # corpus2jsonl might output to outdir directly or a subdirectory
    jsonl_files = list(outdir.glob('*.jsonl'))
    assert len(jsonl_files) >= 1


@pytest.mark.skipif(not HAS_DATASETS, reason='datasets not installed')
def test_cli_create_bio_dataset(tmp_path, input_file):
    # we need a bio_tag_data.jsonl first.
    bio_out = tmp_path / 'bio_tag_for_ds'
    bio_out.mkdir()
    
    with patch.object(sys, 'argv', [
        'konsepy', 'bio-tag', '--input-files', str(input_file),
        '--outdir', str(bio_out), '--package-name', 'example_nlp',
        '--id-label', 'chapter', '--noteid-label', 'chapter'
    ]):
        main()
    
    bio_jsonl = bio_out / 'bio_tag_data.jsonl'
    ds_out = tmp_path / 'dataset_out'
    ds_out.mkdir()

    test_args = [
        'konsepy',
        'create-bio-dataset',
        str(bio_jsonl),
        str(ds_out),
    ]

    with patch.object(sys, 'argv', test_args):
        main()

    # datasets.save_to_disk creates a directory
    ds_dirs = list(ds_out.glob('*.dataset'))
    assert len(ds_dirs) == 1
    assert ds_dirs[0].is_dir()
