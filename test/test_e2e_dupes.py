import json
from konsepy.run_all_matches import run_all_matches

def test_run_all_matches_with_dupe_names(tmp_path):
    # create a mock corpus file with content that matches both branches
    corpus_file = tmp_path / 'corpus.jsonl'
    with open(corpus_file, 'w', encoding='utf8') as f:
        f.write(json.dumps({'chapter': '1', 'notetext': 'Score: 123. Results: 456.'}) + '\n')
    
    outdir = tmp_path / 'out'
    outdir.mkdir()

    result_dir = run_all_matches(
        input_files=[str(corpus_file)],
        outdir=outdir,
        package_name='misc_nlp',
        concepts=['dupe_names'],
        id_label='chapter',
        noteid_label='chapter',
        notetext_label='notetext'
    )

    output_jsonl = result_dir / 'output.jsonl'
    assert output_jsonl.exists()

    with open(output_jsonl, encoding='utf8') as f:
        lines = f.readlines()
        assert len(lines) == 2
        
        # first match (score: 123)
        data1 = json.loads(lines[0])
        assert data1['match'].lower() == 'score: 123'
        assert data1['val'] == '123'
        assert 'val__dup2' not in data1
        
        # second match (results: 456)
        data2 = json.loads(lines[1])
        assert data2['match'].lower() == 'results: 456'
        assert data2['val'] == '456'
        assert 'val__dup2' not in data2
