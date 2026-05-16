import csv
import json
from collections import Counter, defaultdict

from konsepy.regex import extract_categories
from konsepy.results import ExtractionResult
from konsepy.rxsearch import extract_all_regex_target
from konsepy.textio import output_results
from konsepy.run_all_matches import run_all_matches


def _make_score_search():
    import enum
    import re

    class ScoreCategory(enum.Enum):
        SCORE = 1
        UNKNOWN = -1

    def label_score(*, extracted, m, **_):
        group = None
        if m.groupdict():
            group = m.groupdict().get('group')
        if group is not None:
            group = group.lower()
        return ExtractionResult(
            label=ScoreCategory.SCORE,
            value=extracted,
            group=group,
        )

    regexes = [
        (
            re.compile(r'(?P<group>mobility|pain)\s+score\s*:\s*(?P<target>\d+)', re.I),
            None,
            label_score,
        ),
        (
            re.compile(r'\bscore\s*:\s*(?P<target>\d+)\b', re.I),
            None,
            label_score,
        ),
    ]

    return ScoreCategory, extract_all_regex_target(regexes, transform=int)


def test_extract_categories_counts_label_and_collects_extractions():
    ScoreCategory, search = _make_score_search()
    cat_counter_notes = Counter()
    cat_counter_mrns = defaultdict(set)
    noteid_to_cat = defaultdict(Counter)
    mrn_to_cat = defaultdict(Counter)
    extraction_rows = []

    extract_categories(
        'mrn-1',
        'note-1',
        'mobility score: 3 score: 10',
        search,
        cat_counter_mrns=cat_counter_mrns,
        cat_counter_notes=cat_counter_notes,
        mrn_to_cat=mrn_to_cat,
        noteid_to_cat=noteid_to_cat,
        unique_mrns=set(),
        extraction_rows=extraction_rows,
    )

    assert cat_counter_notes[ScoreCategory.SCORE] == 3
    assert mrn_to_cat['mrn-1'][ScoreCategory.SCORE] == 3
    assert noteid_to_cat[('mrn-1', 'note-1')][ScoreCategory.SCORE] == 3
    assert set(cat_counter_mrns[ScoreCategory.SCORE]) == {'mrn-1'}
    assert len(extraction_rows) == 3
    assert {row['value'] for row in extraction_rows} == {3, 10}
    assert any(row['group'] == 'mobility' for row in extraction_rows)
    assert all(row['category'] == str(ScoreCategory.SCORE) for row in extraction_rows)


def test_output_results_writes_extraction_files(tmp_path):
    import enum

    class ScoreCategory(enum.Enum):
        SCORE = 1
        UNKNOWN = -1

    outdir = tmp_path / 'out'
    outdir.mkdir()

    note_counter = Counter({ScoreCategory.SCORE: 3})
    cat_counter_mrns = defaultdict(set)
    cat_counter_mrns[ScoreCategory.SCORE].add('mrn-1')
    mrn_to_cat = defaultdict(Counter)
    mrn_to_cat['mrn-1'][ScoreCategory.SCORE] = 3
    note_to_cat = defaultdict(Counter)
    note_to_cat[('mrn-1', 'note-1')][ScoreCategory.SCORE] = 2
    note_to_cat[('mrn-1', 'note-2')][ScoreCategory.SCORE] = 1

    extraction_rows = [
        {'mrn': 'mrn-1', 'note_id': 'note-1', 'category': 'ScoreCategory.SCORE', 'value': 3, 'group': 'mobility'},
        {'mrn': 'mrn-1', 'note_id': 'note-1', 'category': 'ScoreCategory.SCORE', 'value': 5, 'group': 'mobility'},
        {'mrn': 'mrn-1', 'note_id': 'note-1', 'category': 'ScoreCategory.SCORE', 'value': 2, 'group': 'pain'},
        {'mrn': 'mrn-1', 'note_id': 'note-2', 'category': 'ScoreCategory.SCORE', 'value': 10, 'group': None},
    ]

    output_results(
        outdir,
        note_counter=note_counter,
        cat_counter_mrns=cat_counter_mrns,
        category_enums=[ScoreCategory],
        note_to_cat=note_to_cat,
        mrn_to_cat=mrn_to_cat,
        extraction_rows=extraction_rows,
    )

    with open(outdir / 'extracted_values.csv', newline='') as fh:
        extracted_values = list(csv.DictReader(fh))
    assert len(extracted_values) == 4

    with open(outdir / 'extracted_max_per_note.csv', newline='') as fh:
        max_per_note = list(csv.DictReader(fh))
    assert any(
        row['mrn'] == 'mrn-1'
        and row['note_id'] == 'note-1'
        and row['category'] == 'ScoreCategory.SCORE'
        and row['max_value'] == '5'
        for row in max_per_note
    )

    with open(outdir / 'extracted_max_per_mrn.csv', newline='') as fh:
        max_per_mrn = list(csv.DictReader(fh))
    assert any(
        row['mrn'] == 'mrn-1'
        and row['category'] == 'ScoreCategory.SCORE'
        and row['max_value'] == '10'
        for row in max_per_mrn
    )

    with open(outdir / 'extracted_sum_of_group_maxima.csv', newline='') as fh:
        sum_of_group_maxima = list(csv.DictReader(fh))
    assert any(
        row['mrn'] == 'mrn-1'
        and row['category'] == 'ScoreCategory.SCORE'
        and row['sum_of_group_maxima'] == '7'
        for row in sum_of_group_maxima
    )


def test_run_all_matches_outputs_label_string(tmp_path):
    input_file = tmp_path / 'score_input.jsonl'
    input_file.write_text(
        json.dumps({'chapter': '1', 'text': 'score: 10 mobility score: 3'}) + '\n',
        encoding='utf8',
    )

    outdir = tmp_path / 'out'
    outdir.mkdir()

    result_dir = run_all_matches(
        input_files=[str(input_file)],
        outdir=outdir,
        package_name='misc_nlp',
        concepts=['score_extract'],
        id_label='chapter',
        noteid_label='chapter',
        notetext_label='text',
    )

    rows = []
    with open(result_dir / 'output.jsonl', encoding='utf8') as f:
        for line in f:
            rows.append(json.loads(line))

    assert len(rows) == 3
    assert all(row['category'] == 'ScoreCategory.SCORE' for row in rows)


def test_extract_all_regex_target_wraps_enum_label():
    import enum
    import re

    class ScoreCategory(enum.Enum):
        SCORE = 1

    regexes = [
        (
            re.compile(r'\bscore\s*:\s*(?P<target>\d+)\b', re.I),
            ScoreCategory.SCORE,
        ),
    ]

    search = extract_all_regex_target(regexes, transform=int)
    results = list(search('score: 10'))

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, ExtractionResult)
    assert result.label == ScoreCategory.SCORE
    assert result.value == 10


def test_extract_all_regex_target_allows_postprocessor_override():
    import enum
    import re

    class ScoreCategory(enum.Enum):
        SCORE = 1

    def override(*, extracted, **_):
        return ExtractionResult(label=ScoreCategory.SCORE, value=extracted * 2)

    regexes = [
        (
            re.compile(r'\bscore\s*:\s*(?P<target>\d+)\b', re.I),
            ScoreCategory.SCORE,
            override,
        ),
    ]

    search = extract_all_regex_target(regexes, transform=int)
    results = list(search('score: 10'))

    assert len(results) == 1
    result = results[0]
    assert isinstance(result, ExtractionResult)
    assert result.label == ScoreCategory.SCORE
    assert result.value == 20
