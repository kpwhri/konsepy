import json

import pytest

from konsepy.create_bio_dataset import create_bio_dataset


@pytest.mark.skipif(pytest.importorskip('datasets', reason='datasets not installed') is None,
                    reason='datasets not installed')
def test_create_bio_dataset_handles_empty_results(tmp_path):
    input_file = tmp_path / 'aino.jsonl'
    outpath = tmp_path / 'dataset'
    outpath.mkdir()

    input_file.write_text(
        json.dumps({
            'note_id': 'note-1',
            'text': 'Aino walks home.',
            'results': [],
        }) + '\n',
        encoding='utf8',
    )

    create_bio_dataset(
        input_file,
        outpath,
        test_size=0,
        validation_size=0.5,
    )

    assert len(list(outpath.glob('*.dataset'))) == 1
