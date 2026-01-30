import datetime
from loguru import logger
from konsepy.importer import get_all_concepts
from konsepy.textio import iterate_csv_file
from konsepy.constants import NOTEDATE_LABEL, ID_LABEL, NOTEID_LABEL, NOTETEXT_LABEL

class ProcessingEngine:
    def __init__(self, input_files, package_name, *,
                 encoding='latin1', id_label=ID_LABEL, noteid_label=NOTEID_LABEL,
                 notedate_label=NOTEDATE_LABEL, notetext_label=NOTETEXT_LABEL,
                 noteorder_label=None, metadata_labels=None,
                 concepts=None, limit_noteids=None, start_after=0, stop_after=None,
                 select_probability=1.0, **kwargs):
        self.input_files = input_files
        self.package_name = package_name
        self.encoding = encoding
        self.id_label = id_label
        self.noteid_label = noteid_label
        self.notedate_label = notedate_label
        self.notetext_label = notetext_label
        self.noteorder_label = noteorder_label
        self.metadata_labels = metadata_labels
        self.limit_noteids = limit_noteids
        self.start_after = start_after
        self.stop_after = stop_after
        self.select_probability = select_probability
        self.kwargs = kwargs

        self.concepts = list(get_all_concepts(package_name, *(concepts or list())))
        logger.info(f'Loaded {len(self.concepts)} concepts for processing.')

    def run(self, callback):
        """
        callback: function(studyid, note_id, note_date, text, metadata, concept, categories, matches)
        """
        count = 0
        for count, studyid, note_id, note_date, text, metadata in iterate_csv_file(
                self.input_files, encoding=self.encoding,
                id_label=self.id_label, noteid_label=self.noteid_label,
                notedate_label=self.notedate_label, notetext_label=self.notetext_label,
                noteorder_label=self.noteorder_label, metadata_labels=self.metadata_labels,
                start_after=self.start_after, stop_after=self.stop_after,
                select_probability=self.select_probability
        ):
            if self.limit_noteids and note_id not in self.limit_noteids:
                continue
            
            if count % 50000 == 0:
                 logger.info(f'Completed {count:,} records ({datetime.datetime.now()})')

            for concept in self.concepts:
                categories, matches = concept.run_func(text, include_match=True, **metadata)
                callback(studyid, note_id, note_date, text, metadata, concept, categories, matches)
        
        logger.info(f'Finished. Total records: {count:,} ({datetime.datetime.now()})')
