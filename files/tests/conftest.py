from pathlib import Path

import pytest
from web_conductor.compose import ComposeFileGroup
from web_conductor.config import Config

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / 'fixtures'


@pytest.fixture(scope='session')
def wc_config():
    return Config.load(FIXTURES_DIR)


@pytest.fixture(
    scope='session',
    params=set(p.name for p in FIXTURES_DIR.rglob('compose.*.yml')),
)
def wc_compose_group(request, wc_config):
    paths = list(filter(lambda p: p.exists(), [
        Path(wc_config.root_dir) / request.param,
        Path(wc_config.user_dir) / request.param,
    ]))
    return ComposeFileGroup(request.param, paths)
