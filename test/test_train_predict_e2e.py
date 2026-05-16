import json

import pytest

from konsepy.create_bio_dataset import create_bio_dataset
from konsepy import predict_bio_dataset as predict_mod
from konsepy import train_on_bio_dataset as train_mod

TEXT = 'Ilmatar gave birth to Väinämöinen.'


def _write_training_jsonl(path, count=10):
    ilmatar_start = TEXT.index('Ilmatar')
    ilmatar_end = ilmatar_start + len('Ilmatar')
    vainamoinen_start = TEXT.index('Väinämöinen')
    vainamoinen_end = vainamoinen_start + len('Väinämöinen')

    with open(path, 'w', encoding='utf8') as out:
        for index in range(count):
            out.write(json.dumps({
                'note_id': f'note-{index}',
                'text': TEXT,
                'results': [
                    {
                        'domain': 'hero',
                        'start': ilmatar_start,
                        'end': ilmatar_end,
                    },
                    {
                        'domain': 'hero',
                        'start': vainamoinen_start,
                        'end': vainamoinen_end,
                    },
                ],
            }) + '\n')


def _get_created_dataset_path(outdir):
    dataset_paths = list(outdir.glob('*.dataset'))
    assert len(dataset_paths) == 1
    return dataset_paths[0]


@pytest.mark.skipif(
    train_mod.AutoTokenizer is None
    or train_mod.TrainingArguments is None
    or train_mod.Trainer is None
    or train_mod.DatasetDict is None
    or train_mod.evaluate is None
    or train_mod.np is None,
    reason='training dependencies not installed',
)
@pytest.mark.skipif(
    predict_mod.AutoTokenizer is None
    or predict_mod.AutoModelForTokenClassification is None
    or predict_mod.torch is None,
    reason='prediction dependencies not installed',
)
@pytest.mark.skipif(
    create_bio_dataset.__globals__.get('Dataset') is None,
    reason='datasets not installed',
)
def test_create_train_predict_bio_dataset_e2e(tmp_path, bio_model_path):
    source_path = tmp_path / 'bio_source.jsonl'
    dataset_outdir = tmp_path / 'datasets'
    model_outdir = tmp_path / 'models'
    prediction_outdir = tmp_path / 'predictions'

    dataset_outdir.mkdir()
    model_outdir.mkdir()

    _write_training_jsonl(source_path)

    create_bio_dataset(
        path=source_path,
        outpath=dataset_outdir,
        test_size=0.2,
        validation_size=0.2,
    )

    dataset_path = _get_created_dataset_path(dataset_outdir)

    train_mod.train_on_bio_dataset(
        dataset_path=dataset_path,
        outpath=model_outdir,
        run_name='ilmatar_hero',
        pretrained_model=bio_model_path,
        pretrained_tokenizer=bio_model_path,
        num_train_epochs=3,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=1,
        logging_strategy='no',
        save_strategy='no',
        report_to=[],
    )

    input_file = tmp_path / 'notes.jsonl'
    input_file.write_text(
        json.dumps({
            'studyid': '1',
            'note_id': 'note-1',
            'note_date': '2026-05-15',
            'text': TEXT,
        }) + '\n',
        encoding='utf8',
    )

    output_path = predict_mod.predict_bio_dataset(
        input_files=[input_file],
        outdir=prediction_outdir,
        model_path=model_outdir / 'ilmatar_hero.model',
        id_label='studyid',
        noteid_label='note_id',
        notedate_label='note_date',
        notetext_label='text',
        device='cpu',
    )

    rows = [
        json.loads(line)
        for line in output_path.read_text(encoding='utf8').splitlines()
    ]

    assert len(rows) == 1

    row = rows[0]
    assert row['studyid'] == '1'
    assert row['note_id'] == 'note-1'
    assert row['note_date'] == '2026-05-15'
    assert row['text'] == TEXT
    assert isinstance(row['results'], list)

    for result in row['results']:
        assert set(result) == {'domain', 'capture', 'start', 'end'}
        assert isinstance(result['domain'], str)
        assert isinstance(result['capture'], str)
        assert isinstance(result['start'], int)
        assert isinstance(result['end'], int)
        assert 0 <= result['start'] <= result['end'] <= len(TEXT)
        assert result['capture'] == TEXT[result['start']:result['end']]

    results = row['results']
    # ensure near results have all been merged
    # this handles bpe models like roberta-base
    for index in range(len(results) - 1):
        current = results[index]
        nxt = results[index + 1]
        assert not (
            current['domain'] == nxt['domain'] and current['end'] >= nxt['start']
        )

    assert any(result['domain'] == 'hero' for result in row['results'])
