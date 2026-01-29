import logging
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
