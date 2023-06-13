import importlib
import pkgutil
from enum import EnumMeta
from pathlib import Path

from loguru import logger


class ConceptImport:

    def __init__(self, module_info, package_name):
        self.name = module_info.name
        self.imp = importlib.import_module(f'{package_name}.concepts.{self.name}')
        self.category_enum = self._get_category()
        self.run_func = self.imp.RUN_REGEXES_FUNC
        self.regexes = self.imp.REGEXES

    def run(self, sentence):
        self.run_func(sentence)

    @property
    def domain(self):
        return self.name

    @property
    def categories(self):
        return [category.name for category in self.category_enum]

    def _get_category(self):
        for name, value in self.imp.__dict__.items():
            if isinstance(value, EnumMeta):
                return value
        raise ValueError(f'Unable to identify category enum for concept "{self.name}".')

    def __str__(self):
        return f'ConceptImport<{self.name}>'


def get_all_concepts(package_name: str, *concepts):
    imp = importlib.import_module(f'{package_name}.concepts')
    path = Path(imp.__file__).parent
    for module_info in pkgutil.iter_modules([path]):
        if concepts and module_info.name not in concepts:
            continue  # look for only requested concepts if any supplied
        try:
            yield ConceptImport(module_info, package_name)
        except ValueError as ve:
            logger.warning(f'Failed to load concept: {package_name}.concepts.{module_info.name}')
            logger.exception(ve)
