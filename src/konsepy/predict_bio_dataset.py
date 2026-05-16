import argparse
import json
from pathlib import Path

from loguru import logger
from transformers import AutoModelForTokenClassification, AutoTokenizer

from konsepy.cli import add_outdir_and_infiles, clean_args
from konsepy.constants import ID_LABEL, NOTEID_LABEL, NOTEDATE_LABEL, NOTETEXT_LABEL
from konsepy.textio import iterate_csv_file
try:
    import torch
except ImportError:  # pragma: no cover - optional dependency
    torch = None


def _load_id2label(path: Path):
    with open(path, encoding='utf8') as fh:
        data = json.load(fh)

    return {int(key): value for key, value in data.items()}


def _strip_bio_prefix(label):
    if label == 'O':
        return None

    if '-' not in label:
        return label

    prefix, entity = label.split('-', 1)
    if prefix in {'B', 'I'}:
        return entity

    return label


def _iter_spans_from_labels_and_offsets(labels, offsets, *, merge_subwords=True):
    current = None

    for label, offset in zip(labels, offsets):
        start, end = offset

        if start == end:
            continue

        entity = _strip_bio_prefix(label)

        if entity is None:
            if current is not None:
                yield current
                current = None
            continue

        is_begin = label.startswith('B-')

        if current is None:
            current = {
                'domain': entity,
                'start': start,
                'end': end,
            }
            continue

        if current['domain'] != entity or start > current['end'] or (is_begin and not merge_subwords):
            yield current
            current = {
                'domain': entity,
                'start': start,
                'end': end,
            }
        else:
            current['end'] = end

    if current is not None:
        yield current


def _iter_predicted_spans(
        text,
        tokenizer,
        model,
        id2label,
        *,
        max_length=512,
        device='cpu',
        merge_subwords=True,
):
    if torch is None:
        raise ImportError('predict_bio_dataset requires torch to be installed.')
    encoded = tokenizer(
        text,
        return_offsets_mapping=True,
        return_tensors='pt',
        truncation=True,
        max_length=max_length,
    )

    offset_mapping = encoded.pop('offset_mapping')[0].tolist()
    encoded = {key: value.to(device) for key, value in encoded.items()}

    with torch.no_grad():
        logits = model(**encoded).logits[0]

    predicted_ids = logits.argmax(dim=-1).tolist()
    labels = [id2label[label_id] for label_id in predicted_ids]

    yield from _iter_spans_from_labels_and_offsets(
        labels,
        offset_mapping,
        merge_subwords=merge_subwords,
    )


def predict_bio_dataset(
        input_files,
        outdir: Path,
        model_path: Path,
        *,
        tokenizer_path: Path = None,
        id2label_path: Path = None,
        encoding='utf8',
        id_label=ID_LABEL,
        noteid_label=NOTEID_LABEL,
        notedate_label=NOTEDATE_LABEL,
        notetext_label=NOTETEXT_LABEL,
        noteorder_label=None,
        metadata_labels=None,
        max_length=512,
        device=None,
        merge_subwords=True,
):
    """Run a trained BIO token-classification model over raw input files."""
    outdir.mkdir(parents=True, exist_ok=True)

    tokenizer_path = tokenizer_path or model_path
    id2label_path = id2label_path or model_path.parent / 'id2label.json'
    if device is None:
        device = 'cpu' if torch is None else ('cuda' if torch.cuda.is_available() else 'cpu')

    logger.info(f'Loading tokenizer from {tokenizer_path}')
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    logger.info(f'Loading model from {model_path}')
    model = AutoModelForTokenClassification.from_pretrained(model_path)
    model.to(device)
    model.eval()

    logger.info(f'Loading labels from {id2label_path}')
    id2label = _load_id2label(id2label_path)

    output_path = outdir / 'predictions.jsonl'

    with open(output_path, 'w', encoding='utf8') as out:
        for _, studyid, note_id, note_date, text, metadata in iterate_csv_file(
                input_files,
                encoding=encoding,
                id_label=id_label,
                noteid_label=noteid_label,
                notedate_label=notedate_label,
                notetext_label=notetext_label,
                noteorder_label=noteorder_label,
                metadata_labels=metadata_labels,
        ):
            results = []

            for span in _iter_predicted_spans(
                    text,
                    tokenizer,
                    model,
                    id2label,
                    max_length=max_length,
                    device=device,
                    merge_subwords=merge_subwords,
            ):
                start = span['start']
                end = span['end']
                results.append({
                    'domain': span['domain'],
                    'capture': text[start:end],
                    'start': start,
                    'end': end,
                })

            row = {
                'studyid': studyid,
                'note_id': note_id,
                'note_date': note_date,
                'text': text,
                'results': results,
            }

            if metadata:
                row.update(metadata)

            out.write(json.dumps(row) + '\n')

    logger.info(f'Wrote predictions to {output_path}')
    return output_path


def predict_bio_dataset_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    add_outdir_and_infiles(parser)
    parser.add_argument('model_path', type=Path, help='Path to trained token-classification model.')
    parser.add_argument('--tokenizer-path', type=Path, help='Path to tokenizer. Defaults to model path.')
    parser.add_argument('--id2label-path', type=Path, help='Path to id2label.json. Defaults to model parent directory.')
    parser.add_argument('--encoding', default='utf8')
    parser.add_argument('--id-label', default=ID_LABEL)
    parser.add_argument('--noteid-label', default=NOTEID_LABEL)
    parser.add_argument('--notedate-label', default=NOTEDATE_LABEL)
    parser.add_argument('--notetext-label', default=NOTETEXT_LABEL)
    parser.add_argument('--noteorder-label')
    parser.add_argument('--max-length', type=int, default=512)
    parser.add_argument('--device', help='Device to use, e.g. cpu, cuda, cuda:0.')
    parser.add_argument(
        '--no-merge-subwords',
        action='store_true',
        help='Preserve raw token-level spans instead of merging adjacent subword pieces.',
    )

    args = clean_args(vars(parser.parse_args()))
    args['merge_subwords'] = not args.pop('no_merge_subwords')
    predict_bio_dataset(**args)


if __name__ == '__main__':
    predict_bio_dataset_args()
