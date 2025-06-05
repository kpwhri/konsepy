import json
from pathlib import Path

from konsepy.run4snippets import run4snippets


def test_run4snippets(tmp_path, request):
    input_file = Path(request.fspath).parent / 'data' / 'corpus.jsonl'
    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
    )
    exp_keys = {'note_id', 'concept', 'category', 'studyid', 'note_date', 'match', 'start_index',
                'end_index', 'precontext', 'postcontext', 'pretext', 'posttext'}
    with open(outdir / 'output.jsonl', encoding='utf8') as fh:
        for line in fh:
            data = json.loads(line)
            assert set(data.keys()) == exp_keys
