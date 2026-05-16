import json

from konsepy.predict_bio_dataset import (
    _iter_spans_from_labels_and_offsets,
    _load_id2label,
    _strip_bio_prefix,
)


def test_strip_bio_prefix_returns_none_for_o():
    assert _strip_bio_prefix('O') is None


def test_strip_bio_prefix_removes_begin_prefix():
    assert _strip_bio_prefix('B-hero') == 'hero'


def test_strip_bio_prefix_removes_inside_prefix():
    assert _strip_bio_prefix('I-hero') == 'hero'


def test_strip_bio_prefix_keeps_unprefixed_label():
    assert _strip_bio_prefix('hero') == 'hero'


def test_iter_spans_combines_begin_and_inside_tokens():
    labels = ['B-hero', 'I-hero', 'O']
    offsets = [(0, 4), (4, 11), (12, 16)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 11,
        },
    ]


def test_iter_spans_splits_repeated_begin_tags():
    labels = ['B-hero', 'B-hero']
    offsets = [(0, 4), (5, 10)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 4,
        },
        {
            'domain': 'hero',
            'start': 5,
            'end': 10,
        },
    ]


def test_iter_spans_splits_different_domains():
    labels = ['B-hero', 'I-place']
    offsets = [(0, 11), (15, 23)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 11,
        },
        {
            'domain': 'place',
            'start': 15,
            'end': 23,
        },
    ]


def test_iter_spans_ends_current_span_on_o_label():
    labels = ['B-hero', 'O', 'B-place']
    offsets = [(0, 11), (12, 16), (20, 28)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 11,
        },
        {
            'domain': 'place',
            'start': 20,
            'end': 28,
        },
    ]


def test_iter_spans_ignores_special_token_offsets():
    labels = ['O', 'B-hero', 'I-hero', 'O']
    offsets = [(0, 0), (0, 4), (4, 11), (0, 0)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 11,
        },
    ]


def test_iter_spans_splits_when_offsets_are_not_contiguous():
    labels = ['B-hero', 'I-hero']
    offsets = [(0, 4), (6, 11)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 4,
        },
        {
            'domain': 'hero',
            'start': 6,
            'end': 11,
        },
    ]


def test_iter_spans_allows_unprefixed_entity_labels():
    labels = ['hero', 'hero', 'O']
    offsets = [(0, 4), (4, 11), (12, 16)]

    spans = list(_iter_spans_from_labels_and_offsets(labels, offsets))

    assert spans == [
        {
            'domain': 'hero',
            'start': 0,
            'end': 11,
        },
    ]


def test_load_id2label_converts_json_keys_to_ints(tmp_path):
    path = tmp_path / 'id2label.json'
    path.write_text(
        json.dumps({
            '0': 'O',
            '1': 'B-hero',
            '2': 'I-hero',
        }),
        encoding='utf8',
    )

    id2label = _load_id2label(path)

    assert id2label == {
        0: 'O',
        1: 'B-hero',
        2: 'I-hero',
    }


import json

from konsepy import predict_bio_dataset as mod


class FakeModel:
    def to(self, device):
        return self

    def eval(self):
        return self


def test_predict_bio_dataset_writes_predictions_jsonl(tmp_path, monkeypatch):
    input_file = tmp_path / 'notes.jsonl'
    input_file.write_text(
        json.dumps({
            'studyid': '1',
            'note_id': 'note-1',
            'note_date': '2026-05-15',
            'text': 'Väinämöinen sang in Kalevala.',
        }) + '\n',
        encoding='utf8',
    )

    model_path = tmp_path / 'model'
    model_path.mkdir()

    id2label_path = tmp_path / 'id2label.json'
    id2label_path.write_text(json.dumps({'0': 'O', '1': 'B-hero'}), encoding='utf8')

    monkeypatch.setattr(mod.AutoTokenizer, 'from_pretrained', lambda *_args, **_kwargs: object())
    monkeypatch.setattr(mod.AutoModelForTokenClassification, 'from_pretrained', lambda *_args, **_kwargs: FakeModel())

    def fake_iter_predicted_spans(*_args, **_kwargs):
        yield {
            'domain': 'hero',
            'start': 0,
            'end': 11,
        }
        yield {
            'domain': 'place',
            'start': 20,
            'end': 28,
        }

    monkeypatch.setattr(mod, '_iter_predicted_spans', fake_iter_predicted_spans)

    output_path = mod.predict_bio_dataset(
        input_files=[input_file],
        outdir=tmp_path / 'out',
        model_path=model_path,
        id2label_path=id2label_path,
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

    assert rows == [
        {
            'studyid': '1',
            'note_id': 'note-1',
            'note_date': '2026-05-15',
            'text': 'Väinämöinen sang in Kalevala.',
            'results': [
                {
                    'domain': 'hero',
                    'capture': 'Väinämöinen',
                    'start': 0,
                    'end': 11,
                },
                {
                    'domain': 'place',
                    'capture': 'Kalevala',
                    'start': 20,
                    'end': 28,
                },
            ],
        },
    ]
