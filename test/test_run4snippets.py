import json
from pathlib import Path

from konsepy.run4snippets import run4snippets


def test_run4snippets(tmp_path, request, caplog):
    input_file = Path(request.fspath).parent / 'data' / 'corpus.jsonl'
    outdir = run4snippets(
        [input_file],
        outdir=tmp_path,
        package_name='example_nlp',
        id_label='chapter',
        noteid_label='chapter',
    )
    # test log results
    loglines = caplog.text.split('\n')
    assert 'Arguments ignored: {}' in loglines[0]
    assert 'Loaded 3 concepts for processing' in loglines[1]
    assert 'Total records: 117' in loglines[2]

    # test jsonlines output
    exp_keys = {'note_id', 'concept', 'category', 'studyid', 'note_date', 'match', 'start_index',
                'end_index', 'precontext', 'postcontext', 'pretext', 'posttext'}
    with open(outdir / 'output.jsonl', encoding='utf8') as fh:
        for line in fh:
            data = json.loads(line)
            assert set(data.keys()) == exp_keys
