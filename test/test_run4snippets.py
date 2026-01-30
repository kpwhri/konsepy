import json
from pathlib import Path

import pytest

from konsepy.run4snippets import run4snippets


@pytest.fixture
def input_file(request):
    return Path(request.fspath).parent / 'data' / 'corpus.jsonl'


def iter_jsonl_output(outdir: Path, extra_keys=None):
    extra_keys = set(extra_keys) if extra_keys else set()
    exp_keys = {'note_id', 'concept', 'category', 'studyid', 'note_date', 'match', 'start_index',
                'end_index', 'precontext', 'postcontext', 'pretext', 'posttext'} | extra_keys
    with open(outdir / 'output.jsonl', encoding='utf8') as fh:
        for line in fh:
            data = json.loads(line)
            assert set(data.keys()) == exp_keys
            yield data


def test_run4snippets(tmp_path, input_file, caplog):
    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
    )
    # test log results
    loglines = [line for line in caplog.text.split('\n') if line.strip()]
    assert any('Arguments ignored: {}' in line for line in loglines)
    assert any('Loaded 3 concepts for processing' in line for line in loglines)
    assert any('Output 713 rows' in line for line in loglines)
    assert any('Total records: 117' in line for line in loglines)

    # test jsonlines output
    for data in iter_jsonl_output(outdir):
        pass


def test_run4snippets_with_metadata(tmp_path, input_file, caplog):
    metadata = ['chapter', 'title']
    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
        order_metadata=metadata,
        metadata_labels=metadata,
    )
    # test log results
    loglines = [line for line in caplog.text.split('\n') if line.strip()]
    assert any('Arguments ignored: {}' in line for line in loglines)
    assert any('Loaded 3 concepts for processing' in line for line in loglines)
    assert any('Output 713 rows' in line for line in loglines)
    assert any('Total records: 117' in line for line in loglines)

    # test jsonlines output
    for data in iter_jsonl_output(outdir, extra_keys=set(metadata)):
        assert metadata[0] in data.keys()  # confirm presence
        assert metadata[0] == list(data.keys())[0]  # ensure this is in the correct order
        assert metadata[1] in data.keys()  # confirm presence
        assert metadata[1] == list(data.keys())[1]  # ensure this is in the correct order


def test_run4snippets_only_categories(tmp_path, input_file, caplog):
    target_categories = ['Jealous.NO', 'Revenge.NO', 'Justice.NO']
    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
        target_categories=target_categories,
    )
    # test log results
    loglines = [line for line in caplog.text.split('\n') if line.strip()]
    assert any('Arguments ignored: {}' in line for line in loglines)
    assert any('Loaded 3 concepts for processing' in line for line in loglines)
    assert any('Output 4 rows' in line for line in loglines)
    assert any('Total records: 117' in line for line in loglines)

    # test jsonlines output
    for data in iter_jsonl_output(outdir):
        assert data['category'] in target_categories


def test_run4snippets_only_concepts(tmp_path, input_file, caplog):
    target_concepts = ['justice']
    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
        target_concepts=target_concepts,
    )
    # test log results
    loglines = [line for line in caplog.text.split('\n') if line.strip()]
    assert any('Arguments ignored: {}' in line for line in loglines)
    assert any('Loaded 3 concepts for processing' in line for line in loglines)
    assert any('Output 536 rows' in line for line in loglines)
    assert any('Total records: 117' in line for line in loglines)

    # test jsonlines output
    for data in iter_jsonl_output(outdir):
        assert data['concept'] in target_concepts


def test_run4snippets_only_concepts_and_categories(tmp_path, input_file, caplog):
    target_concepts = ['revenge']
    target_categories = ['Jealous.FAMILY']

    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
        target_concepts=target_concepts,
        target_categories=target_categories,
    )
    # test log results
    loglines = [line for line in caplog.text.split('\n') if line.strip()]
    assert any('Arguments ignored: {}' in line for line in loglines)
    assert any('Loaded 3 concepts for processing' in line for line in loglines)
    assert any('Output 135 rows' in line for line in loglines)
    assert any('Total records: 117' in line for line in loglines)

    # test jsonlines output
    for data in iter_jsonl_output(outdir):
        assert data['concept'] in target_concepts or data['category'] in target_categories
