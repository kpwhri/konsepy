
# konsepy

Framework for build NLP information extraction systems using regular expressions. `konsepy` then enables leveraging the NLP system to create a silver standard for fine-tuning a transformer model. 

## Installation

* `konsepy` is designed to be used with the [`knosepy_nlp_template`](https://github.com/kpwhri/konsepy_nlp_template)
  * See the README there for current installation instructions.
* To use `konsepy` as a standalone entity:
  * Install with `pip`:
    * `pip install konsepy[all]`
    * For sentence-splitting corpora from fine-tuning a sentence based transformer, `spacy` will also need to be installed and configured.

## Usage

The package provides a centralized CLI tool `konsepy`.

### Building your NLP Package

To use `konsepy`, you need to create an NLP package (e.g., `my_nlp_package`) with the following structure. The best way to get this format is to clone the [konsepy_nlp_template](https://github.com/kpwhri/konsepy_nlp_template):

```text
my_nlp_package/
├── __init__.py
└── concepts/
    ├── __init__.py
    └── my_concept.py
```

Each concept file (e.g., `my_concept.py`) must define:
* `REGEXES`: A list of regex-category pairs.
* `RUN_REGEXES_FUNC`: A function that executes the regexes and returns categories/matches.
* `CategoryEnum`: An `Enum` defining the possible categories for the concept.

### Running konsepy

```bash
# Run all concepts in a package against input files
konsepy run-all --package-name my_nlp_package --input-files data.csv --outdir output/

# Extract snippets for manual review
konsepy run4snippets --package-name my_nlp_package --input-files data.csv --outdir snippets/

# Generate BIO tagged data for model training
konsepy bio-tag --package-name my_nlp_package --input-files data.csv --outdir bio_data/
```

For more detailed documentation and a template, see [konsepy_nlp_template](https://github.com/kpwhri/konsepy_nlp_template).


## Roadmap

* Change labels to some metadata object to allow more diverse input sources and run info
