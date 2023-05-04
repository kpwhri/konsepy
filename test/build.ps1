# Test script: run from this test directory to ensure that everything works.
git clone https://github.com/kpwhri/konsepy_nlp_template
cd konsepy_nlp_template
python -m venv .venv
.venv/scripts/activate.ps1
pip install requirements.txt
pip install ../..
$env:PYTHONPATH='src'
cp templates/new_concept_template.py src/example_nlp/concepts/new_concept_template.py
(Get-Content src/example_nlp/concepts/new_concept_template.py) `
    -creplace 'concept', '(lonely|isolated)' |
  Out-File -encoding utf8 src/example_nlp/concepts/new_concept_template.py
cp templates/test_concept_template.py tests/test_concept_template.py
(Get-Content tests/test_concept_template.py) `
    -creplace 'Text excerpt containing concept.', 'He feels lonely.' |
  Out-File -encoding utf8 tests/test_concept_template.py
pytest tests
mkdir out
python src/get_text_snippets.py --input-files sample/corpus.csv --outdir out/corpus_snippet --regexes 'LONELY==(lonely|isolated)'
python src/get_text_snippets.py --input-files sample/corpus_lined.csv --outdir out/lined_corpus_snippet --regexes 'LONELY==(lonely|isolated)' --noteorder-label note_line
python src/run_all.py --input-files sample/corpus.csv --outdir out/run
python src/run_all.py --input-files sample/corpus_lined.csv --outdir out/run_lined --noteorder-label note_line
