import importlib
import inspect
import pkgutil
from enum import EnumMeta
from pathlib import Path

from loguru import logger


class ConceptImport:

    def __init__(self, module_info, package_name):
        self.name = module_info.name
        self.imp = importlib.import_module(f'{package_name}.concepts.{self.name}')
        self.category_enums = list(self._get_categories())
        self._run_func = self.imp.RUN_REGEXES_FUNC
        self.regexes = self.imp.REGEXES
        self._params = inspect.signature(self._run_func).parameters

        self.has_include_match = self.has_param('include_match')

    def has_param(self, param, default=False):
        exists = param in self._params
        if not exists:
            logger.warning(f'Concept `{self.name}` is missing `{param}={default}` in RUN_REGEXES_FUNC.')
        return exists

    def run_func(self, text, include_match=True, categories_only=False, **metadata):
        # ensure requested metadata in calling function
        metadata = {k: v for k, v in metadata.items() if k in self._params}
        if include_match and self.has_include_match:
            res = list(self._run_func(text, include_match=include_match, **metadata))
            # matches = [(m.group(), m.start(), m.end()) for _, m in res]
            matches = [m for _, m in res]  # return match directly
            categories = [str(category) for category, _ in res]
        else:
            if self.has_include_match:
                categories = [str(category) for category in self._run_func(text, include_match=False, **metadata)]
            else:
                categories = [str(category) for category in self._run_func(text, **metadata)]
            matches = None
        if categories_only:
            return categories
        return categories, matches

    def run(self, sentence):
        return self.run_func(sentence)

    @property
    def domain(self):
        return self.name

    @property
    def categories(self):
        return [category.name for category_enum in self.category_enums for category in category_enum]

    def _get_categories(self):
        categories = []
        for name, value in self.imp.__dict__.items():
            if isinstance(value, EnumMeta):
                categories.append(value)
        if categories:
            return categories
        else:
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
