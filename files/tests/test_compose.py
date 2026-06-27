import tempfile
from pathlib import Path

import pytest
from src.compose import ComposeFileGroup
from src.config import Config

TESTS_DIR = Path(__file__).parent
FIXTURES_DIR = TESTS_DIR / 'fixtures'


@pytest.mark.parametrize(
    'name',
    {'compose.proxy.yml', 'compose.user.yml'}
    # set(p.name for p in FIXTURES_DIR.rglob('compose.*.yml', recurse_symlinks=True)),
)
def test_files(name, snapshot):
    cfg = Config.load(FIXTURES_DIR)
    paths = list(filter(lambda p: p.exists(), [
        Path(cfg.root_dir) / name,
        Path(cfg.user_dir) / name,
    ]))
    cg = ComposeFileGroup(name, paths, cfg=cfg)
    for i, cf in enumerate(cg.files):
        with tempfile.TemporaryDirectory() as tmp_dir:
            for f in cf.create_merge_files(dir=tmp_dir):
                p = Path(f)
                assert p.read_text() == snapshot(name=f'{i}_{p.name}')
