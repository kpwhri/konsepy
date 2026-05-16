import sqlite3

from konsepy.constants import ID_LABEL, NOTEDATE_LABEL, NOTEID_LABEL, NOTETEXT_LABEL
from konsepy.textio import _extract_sqlite_file, iterate_csv_file


def test_extract_sqlite_file_reads_notes_table(tmp_path):
    input_file = tmp_path / 'vaino.db'

    with sqlite3.connect(input_file) as connection:
        connection.execute(
            f'''
            CREATE TABLE notes (
                "{ID_LABEL}" TEXT,
                "{NOTEID_LABEL}" TEXT,
                "{NOTEDATE_LABEL}" TEXT,
                "{NOTETEXT_LABEL}" TEXT
            )
            '''
        )
        connection.executemany(
            f'''
            INSERT INTO notes (
                "{ID_LABEL}",
                "{NOTEID_LABEL}",
                "{NOTEDATE_LABEL}",
                "{NOTETEXT_LABEL}"
            )
            VALUES (?, ?, ?, ?)
            ''',
            [
                ('vaino', 'note-1', '2026-05-01', 'Vainamoinen sings.'),
                ('ilmarinen', 'note-2', '2026-05-02', 'Ilmarinen forges.'),
            ],
        )

    rows = list(
        _extract_sqlite_file(
            input_file,
            'latin1',
            ID_LABEL,
            NOTEID_LABEL,
            NOTEDATE_LABEL,
            NOTETEXT_LABEL,
        )
    )

    assert rows == [
        ('vaino', 'Vainamoinen sings.', 'note-1', '2026-05-01', '', {}),
        ('ilmarinen', 'Ilmarinen forges.', 'note-2', '2026-05-02', '', {}),
    ]


def test_iterate_csv_file_reads_sqlite_notes_table(tmp_path):
    input_file = tmp_path / 'louhi.sqlite'

    with sqlite3.connect(input_file) as conn:
        conn.execute(
            f'''
            CREATE TABLE notes (
                "{ID_LABEL}" TEXT,
                "{NOTEID_LABEL}" TEXT,
                "{NOTEDATE_LABEL}" TEXT,
                "{NOTETEXT_LABEL}" TEXT
            )
            '''
        )
        conn.executemany(
            f'''
            INSERT INTO notes (
                "{ID_LABEL}",
                "{NOTEID_LABEL}",
                "{NOTEDATE_LABEL}",
                "{NOTETEXT_LABEL}"
            )
            VALUES (?, ?, ?, ?)
            ''',
            [
                ('louhi', 'note-1', '2026-05-03', 'Louhi guards the Sampo.'),
                ('lemminkainen', 'note-2', '2026-05-04', 'Lemminkainen journeys.'),
            ],
        )
        conn.commit()

    rows = list(iterate_csv_file([input_file]))

    assert rows == [
        (1, 'louhi', 'note-1', '2026-05-03', 'Louhi guards the Sampo.', {}),
        (2, 'lemminkainen', 'note-2', '2026-05-04', 'Lemminkainen journeys.', {}),
    ]