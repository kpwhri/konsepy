import pytest

import konsepy.train_on_bio_dataset as train_mod


def test_compute_metrics_requires_evaluate(monkeypatch):
    monkeypatch.setattr(train_mod, 'evaluate', None)
    with pytest.raises(ImportError, match='requires evaluate'):
        train_mod.compute_metrics(([], []), {})


def test_train_on_bio_dataset_requires_datasets(monkeypatch, tmp_path):
    monkeypatch.setattr(train_mod, 'AutoTokenizer', object())
    monkeypatch.setattr(train_mod, 'TrainingArguments', object())
    monkeypatch.setattr(train_mod, 'Trainer', object())
    monkeypatch.setattr(train_mod, 'DatasetDict', None)

    with pytest.raises(ImportError, match='requires datasets'):
        train_mod.train_on_bio_dataset(
            dataset_path=tmp_path / 'missing',
            outpath=tmp_path / 'out',
            run_name='test',
        )
