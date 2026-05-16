import logging
from pathlib import Path
import pytest
from loguru import logger


@pytest.fixture
def caplog(caplog):
    class PropagateHandler(logging.Handler):
        def emit(self, record):
            logging.getLogger(record.name).handle(record)

    handler_id = logger.add(PropagateHandler(), format="{message}")
    yield caplog
    logger.remove(handler_id)


@pytest.fixture
def saiga_antelope():
    return 'Saiga antelope have distinctive bulbous noses. These help filter out dust and regulate their' \
           'body temperature in the harsh climates of Central Asia.'


@pytest.fixture
def basedir() -> Path:
    return Path(__file__).resolve().parent


@pytest.fixture
def datadir(basedir) -> Path:
    return basedir / 'data'


def pytest_addoption(parser):
    parser.addoption(
        '--bio-model-path',
        action='store',
        default=None,
        help='Path to a trained BIO token-classification model for optional end-to-end prediction tests.',
    )


@pytest.fixture
def bio_model_path(request):
    value = request.config.getoption('--bio-model-path')
    if not value:
        pytest.skip('requires --bio-model-path')

    path = Path(value)
    if not path.exists():
        pytest.skip(f'--bio-model-path does not exist: {path}')

    return path
