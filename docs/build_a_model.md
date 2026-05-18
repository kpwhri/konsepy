# Dataset, LLM Training, and LLM Prediction Workflow

This guide shows how to create a BIO token-classification dataset, train a transformer model, and run predictions with
the trained model.

## Install model dependencies

Install the model-related dependencies before running these commands:

```bash
pip install -e ".[model]"
```

If using all optional dependencies:

```bash
pip install -e ".[all]"
```

## Step 1: Prepare BIO source JSONL

`create-bio-dataset` expects JSONL where each line contains:

- `note_id`: unique document/note identifier
- `text`: source text
- `results`: list of labeled spans

Each result should contain:

- `domain`: entity label
- `start`: character start index
- `end`: character end index

Example `bio_source.jsonl`:

```json
{
  "note_id": "note-1",
  "text": "Ilmatar gave birth to Väinämöinen.",
  "results": [
    {
      "domain": "hero",
      "start": 0,
      "end": 7
    },
    {
      "domain": "hero",
      "start": 22,
      "end": 33
    }
  ]
}
```

The text indices are zero-based and `end` is exclusive.

For example:

```text
Ilmatar gave birth to Väinämöinen.
0123456               22222222223
                      23456789012
```

- `Ilmatar` starts at `0` and ends at `7`
- `Väinämöinen` starts at `22` and ends at `33`

For very small experiments, you can duplicate the line several times with different `note_id` values so
train/test/validation splits have enough rows.

## Step 2: Create the BIO dataset

Run:

```bash
konsepy create-bio-dataset path/to/bio_source.jsonl path/to/datasets
```

Example:

```bash
konsepy create-bio-dataset data/bio_source.jsonl output/datasets
```

This creates a Hugging Face `DatasetDict` on disk, with a timestamped directory name such as:

```text
output/datasets/bio_source.20260515_143012.dataset
```

### Useful parameters

```bash
konsepy create-bio-dataset \
  data/bio_source.jsonl \
  output/datasets \
  --test-size 0.1 \
  --validation-size 0.05 \
  --note-id-field note_id
```

Parameters:

| Parameter           |   Default | Meaning                                     |
|---------------------|----------:|---------------------------------------------|
| `path`              |  required | Input BIO JSONL file                        |
| `outpath`           |  required | Directory where the dataset will be written |
| `--test-size`       |     `0.1` | Fraction of data for test split             |
| `--validation-size` |    `0.05` | Fraction of data for validation split       |
| `--note-id-field`   | `note_id` | Field containing note/document IDs          |

## Step 3: Train a model

Use the dataset directory created in Step 2.

```bash
python -m konsepy.train_on_bio_dataset \
  output/datasets/bio_source.20260515_143012.dataset \
  output/models \
  ilmatar_hero \
  --pretrained-model roberta-base \
  --pretrained-tokenizer roberta-base \
  --param num_train_epochs==3 per_device_train_batch_size==1 per_device_eval_batch_size==1 logging_strategy==no save_strategy==no report_to==none
```

This writes a trained model to:

```text
output/models/ilmatar_hero.model
```

It also writes label maps:

```text
output/models/id2label.json
output/models/label2id.json
```

### Recommended pretrained models

For a quick smoke test:

```bash
--pretrained-model hf-internal-testing/tiny-random-roberta
```

For a more realistic model:

```bash
--pretrained-model roberta-base
```

For clinical text, you may prefer a clinical checkpoint:

```bash
--pretrained-model emilyalsentzer/Bio_ClinicalBERT
```

### Common training parameters

```bash
--param \
  num_train_epochs==5 \
  learning_rate==2e-4 \
  per_device_train_batch_size==8 \
  per_device_eval_batch_size==8 \
  logging_steps==100 \
  save_strategy==no
```

For a very small e2e smoke test:

```bash
--param \
  num_train_epochs==3 \
  per_device_train_batch_size==1 \
  per_device_eval_batch_size==1 \
  logging_strategy==no \
  save_strategy==no \
  report_to==none
```

## Step 4: Prepare prediction input

Prediction input is raw note text in JSONL, CSV, TSV, SAS, or another supported input format.

For JSONL, create a file such as `notes.jsonl`:

```json
{
  "studyid": "1",
  "note_id": "note-1",
  "note_date": "2026-05-15",
  "text": "Ilmatar gave birth to Väinämöinen."
}
```

The default field names are:

| Field           | Default     |
|-----------------|-------------|
| study/person ID | `studyid`   |
| note ID         | `note_id`   |
| note date       | `note_date` |
| note text       | `text`      |

## Step 5: Predict with the trained model

Run:

```bash
konsepy predict-bio-dataset \
  output/models/ilmatar_hero.model \
  --input-files data/notes.jsonl \
  --outdir output/predictions
```

This writes:

```text
output/predictions/predictions.jsonl
```

Example output row:

```json
{
  "studyid": "1",
  "note_id": "note-1",
  "note_date": "2026-05-15",
  "text": "Ilmatar gave birth to Väinämöinen.",
  "results": [
    {
      "domain": "hero",
      "capture": "Ilmatar",
      "start": 0,
      "end": 7
    },
    {
      "domain": "hero",
      "capture": "Väinämöinen",
      "start": 22,
      "end": 33
    }
  ]
}
```

## Prediction parameters

```bash
konsepy predict-bio-dataset \
  output/models/ilmatar_hero.model \
  --input-files data/notes.jsonl \
  --outdir output/predictions \
  --id-label studyid \
  --noteid-label note_id \
  --notedate-label note_date \
  --notetext-label text \
  --max-length 512 \
  --device cpu
```

Parameters:

| Parameter             |                      Default | Meaning                                                                   |
|-----------------------|-----------------------------:|---------------------------------------------------------------------------|
| `model_path`          |                     required | Path to trained token-classification model                                |
| `--input-files`       |                     required | Input files to predict over                                               |
| `--outdir`            |                     required | Directory for `predictions.jsonl`                                         |
| `--tokenizer-path`    |                   model path | Optional tokenizer path                                                   |
| `--id2label-path`     | model parent `id2label.json` | Optional label map path                                                   |
| `--encoding`          |                       `utf8` | Input file encoding                                                       |
| `--id-label`          |                    `studyid` | Study/person ID field                                                     |
| `--noteid-label`      |                    `note_id` | Note ID field                                                             |
| `--notedate-label`    |                  `note_date` | Note date field                                                           |
| `--notetext-label`    |                       `text` | Text field                                                                |
| `--noteorder-label`   |                         none | Optional note ordering field                                              |
| `--max-length`        |                        `512` | Maximum model sequence length                                             |
| `--device`            |                         auto | Device, e.g. `cpu`, `cuda`, or `cuda:0`                                   |
| `--no-merge-subwords` |                        false | Preserve raw token-level spans instead of merging adjacent subword pieces |

## Full example

```bash
mkdir -p data output/datasets output/models output/predictions
```

Create `data/bio_source.jsonl`:

```bash
cat > data/bio_source.jsonl <<'EOF'
{"note_id":"note-1","text":"Ilmatar gave birth to Väinämöinen.","results":[{"domain":"hero","start":0,"end":7},{"domain":"hero","start":22,"end":33}]}
{"note_id":"note-2","text":"Ilmatar gave birth to Väinämöinen.","results":[{"domain":"hero","start":0,"end":7},{"domain":"hero","start":22,"end":33}]}
{"note_id":"note-3","text":"Ilmatar gave birth to Väinämöinen.","results":[{"domain":"hero","start":0,"end":7},{"domain":"hero","start":22,"end":33}]}
{"note_id":"note-4","text":"Ilmatar gave birth to Väinämöinen.","results":[{"domain":"hero","start":0,"end":7},{"domain":"hero","start":22,"end":33}]}
{"note_id":"note-5","text":"Ilmatar gave birth to Väinämöinen.","results":[{"domain":"hero","start":0,"end":7},{"domain":"hero","start":22,"end":33}]}
EOF
```

Create the dataset:

```bash
konsepy create-bio-dataset \
  data/bio_source.jsonl \
  output/datasets \
  --test-size 0.2 \
  --validation-size 0.2
```

Find the created dataset path:

```bash
ls output/datasets
```

Train:

```bash
python -m konsepy.train_on_bio_dataset \
  output/datasets/bio_source.YYYYMMDD_HHMMSS.dataset \
  output/models \
  ilmatar_hero \
  --pretrained-model roberta-base \
  --pretrained-tokenizer roberta-base \
  --param num_train_epochs==3 per_device_train_batch_size==1 per_device_eval_batch_size==1 logging_strategy==no save_strategy==no report_to==none
```

Create prediction input:

```bash
cat > data/notes.jsonl <<'EOF'
{"studyid":"1","note_id":"note-1","note_date":"2026-05-15","text":"Ilmatar gave birth to Väinämöinen."}
EOF
```

Predict:

```bash
konsepy predict-bio-dataset \
  output/models/ilmatar_hero.model \
  --input-files data/notes.jsonl \
  --outdir output/predictions \
  --device cpu
```

View predictions:

```bash
cat output/predictions/predictions.jsonl
```

## Notes

- The model output quality depends on the amount and variety of labeled data.
- A tiny duplicated dataset is useful only for testing the pipeline.
- For real use, label many examples with representative text.
- BIO labels are generated from `domain` values in the source JSONL.
- The trained model stores `id2label` and `label2id` in its model config and as JSON files.
