from pathlib import Path

import pytest
from web_conductor.compose import compose_files_find
from web_conductor.config import Config

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / 'fixtures'


@pytest.fixture(scope='session')
def wc_config():
    return Config.load(FIXTURES_DIR)


@pytest.fixture(scope='session')
def wc_compose_collection(wc_config):
    return compose_files_find(wc_config)
