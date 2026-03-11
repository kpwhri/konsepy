import json
from pathlib import Path
from konsepy.run_all_matches import run_all_matches


def test_run_all_matches_direct(tmp_path):
    input_file = Path('test/data/corpus.jsonl')
    outdir = tmp_path / 'direct_run'
    outdir.mkdir()

    result_dir = run_all_matches(
        input_files=[str(input_file)],
        outdir=outdir,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter'
    )

    assert result_dir.exists()
    assert result_dir.name.startswith('run_all_matches_')

    output_jsonl = result_dir / 'output.jsonl'
    assert output_jsonl.exists()

    with open(output_jsonl, encoding='utf8') as f:
        lines = f.readlines()
        assert len(lines) > 0

        for line in lines:
            data = json.loads(line)
            assert 'studyid' in data
            assert 'note_id' in data
            assert 'concept' in data
            assert 'category' in data
            assert 'precontext' in data
            assert 'match' in data
            assert 'postcontext' in data
            assert 'start_index' in data
            assert 'end_index' in data
            # check that it's one match per row (in run_all it was 'categories' list)
            assert 'categories' not in data
            assert isinstance(data['category'], str)


def test_run_all_matches_date_dupe_named_groups(tmp_path):
    input_file = tmp_path / "date_input.jsonl"
    input_file.write_text(
        (
            '{"chapter": "1", "text": "It was the 24th of February, 1815. '
            'Another letter was dated February 25, 1815."}\n'
        ),
        encoding="utf8",
    )

    outdir = tmp_path / "out"
    outdir.mkdir()

    result_dir = run_all_matches(
        input_files=[str(input_file)],
        outdir=outdir,
        package_name="misc_nlp",
        concepts=["date"],
        id_label="chapter",
        noteid_label="chapter",
        notetext_label="text",
    )

    rows = []
    with open(result_dir / "output.jsonl", encoding="utf8") as f:
        for line in f:
            rows.append(json.loads(line))

    date_rows = [row for row in rows if row["concept"] == "date"]
    assert len(date_rows) >= 2

    assert any(
        row["match"] == "24th of February, 1815"
        and row.get("day") == "24"
        and row.get("month").lower() == "february"
        and row.get("year") == "1815"
        for row in date_rows
    )

    assert any(
        row["match"] == "February 25, 1815"
        and row.get("day") == "25"
        and row.get("month").lower() == "february"
        and row.get("year") == "1815"
        for row in date_rows
    )
