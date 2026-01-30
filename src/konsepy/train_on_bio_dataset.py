import argparse
import json
from pathlib import Path

from loguru import logger

from transformers import AutoTokenizer, DataCollatorForTokenClassification, AutoModelForTokenClassification, \
    TrainingArguments, Trainer
from datasets import load_dataset, load_from_disk, DatasetDict, load_metric
import numpy as np


def tokenize_adjust_labels(tokenizer, label2id):
    def _inner_tokenize_adjust_labels(all_samples_per_split):
        """Get values for input_ids, token_type_ids, attention_mask"""
        tokenized_samples = tokenizer.batch_encode_plus(
            all_samples_per_split['tokens'],
            is_split_into_words=True,
            padding='max_length',
            truncation=True,
            max_length=512,
        )
        # tokenized_samples is not a datasets object so this alone won't work with Trainer API, hence map is used
        # so the new keys [input_ids, labels (after adjustment)]
        # can be added to the datasets dict for each train test validation split
        total_adjusted_labels = []
        for k in range(0, len(tokenized_samples['input_ids'])):
            prev_wid = -1
            word_ids_list = tokenized_samples.word_ids(batch_index=k)
            existing_label_ids = all_samples_per_split['ner_tags'][k]
            i = -1
            adjusted_label_ids = []

            for wid in word_ids_list:
                if wid is None:
                    adjusted_label_ids.append(-100)
                elif wid != prev_wid:
                    i = i + 1
                    adjusted_label_ids.append(label2id[existing_label_ids[i]])
                    prev_wid = wid
                else:
                    adjusted_label_ids.append(label2id[existing_label_ids[i]])
            total_adjusted_labels.append(adjusted_label_ids)
        tokenized_samples['labels'] = total_adjusted_labels
        return tokenized_samples

    return _inner_tokenize_adjust_labels


def compute_metrics(p, id2label):
    metric = load_metric('seqeval')
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    # Remove ignored index (special tokens)
    true_predictions = [
        [id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]
    true_labels = [
        [id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = metric.compute(predictions=true_predictions, references=true_labels)
    flattened_results = {
        'overall_precision': results['overall_precision'],
        'overall_recall': results['overall_recall'],
        'overall_f1': results['overall_f1'],
        'overall_accuracy': results['overall_accuracy'],
        'predicted_b': len([x for p in true_predictions for x in p if x.startswith('B')]),
        'predicted_i': len([x for p in true_predictions for x in p if x.startswith('I')]),
        'predicted_o': len([x for p in true_predictions for x in p if x.startswith('O')]),
    }


def train_on_bio_dataset(dataset_path: Path, outpath: Path, run_name: str, pretrained_tokenizer: str = None,
                         pretrained_model: str = 'emilyalsentzer/Bio_ClinicalBERT', **params):
    dataset = DatasetDict.load_from_disk(dataset_path)
    tagset = set([x for doc in dataset['train']['ner_tags'] for x in doc])
    label2id = {x: i for i, x in enumerate(tagset)}
    id2label = {v: k for k, v in label2id.items()}
    tokenizer = AutoTokenizer.from_pretrained(pretrained_tokenizer or pretrained_model)

    tokenized_dataset = dataset.map(tokenize_adjust_labels(tokenizer, label2id), batched=True)
    data_collator = DataCollatorForTokenClassification(
        tokenizer,
        padding='max_length',
        max_length=512,
    )
    model = AutoModelForTokenClassification.from_pretrained(pretrained_model)
    default_params = {
                         'evaluation_strategy': 'steps',
                         'learning_rate': 2e-4,
                         'per_device_train_batch_size': 32,
                         'per_device_eval_batch_size': 32,
                         'num_train_epochs': 50,
                         'weight_decay': 0.01,
                         'logging_steps': 1000,
                         'save_strategy': 'no',
                     } | params
    training_args = TrainingArguments(
        output_dir=str(outpath),
        run_name=run_name,
        **default_params,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset['train'],
        eval_dataset=tokenized_dataset['test'],
        data_collator=data_collator,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics
    )
    trainer.train()
    trainer.save_model(outpath / f'{run_name}.model')
    with open(outpath / 'id2label.json', 'w') as out:
        json.dump(id2label, out)
    with open(outpath / 'label2id.json', 'w') as out:
        json.dump(label2id, out)

    val_results = trainer.predict(tokenized_dataset['validation'])
    logger.info(val_results)
    logger.info(f'Label-2-id: {label2id}')
    logger.info(f'Id-2-label: {id2label}')


def train_on_bio_dataset_args():
    parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
    parser.add_argument('dataset_path', type=Path,
                        help='Path to dataset (output from `create_bio_dataset.py`)')
    parser.add_argument('outpath', type=Path,
                        help='Path to write model to.')
    parser.add_argument('run_name', type=str,
                        help='Name of this run.')
    parser.add_argument('--pretrained-model', dest='pretrained_model', type=str,
                        default='emilyalsentzer/Bio_ClinicalBERT',
                        help='Path to model to fine-tune, or to huggingface model.')
    parser.add_argument('--pretrained-tokenizer', dest='pretrained_tokenizer', type=str,
                        help='Path to tokenizer for model, or to huggingface tokenizer;'
                             ' defaults to same as `pretrained_model`')
    parser.add_argument('--param', nargs='*',
                        help='Parameters to supply to `TrainingArguments` in form of `num_train_epochs==50`')
    args = vars(parser.parse_args())
    params = {x.split('==')[0]: x.split('==')[1] for x in args['param']}
    del args['param']
    train_on_bio_dataset(**args, **params)


if __name__ == '__main__':
    train_on_bio_dataset_args()
