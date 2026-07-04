import os

from web_conductor.compose import compose_merge
from web_conductor.utils import yaml_dump


def test_files(wc_config, wc_compose_group, snapshot):
    """test each file layer independently, and the original file"""
    for i, cf in enumerate(wc_compose_group.files):
        # generated layers
        for name, data in cf.create_layers(wc_config, os.path.dirname(cf.path)):
            assert yaml_dump(data) == snapshot(name=f'{i}_{name}')
        # original file
        assert yaml_dump(cf.yml) == snapshot(name=f'{i}_{os.path.basename(cf.path)}')


def test_merged(wc_config, wc_compose_group, snapshot):
    """test the merged result of all compose files in the group"""
    merged_yml = {}
    for _, yml in wc_compose_group.create_layers(wc_config, os.path.dirname(wc_compose_group.files[0].path)):
        merged_yml = compose_merge(merged_yml, yml)
    for f in wc_compose_group.files:
        merged_yml = compose_merge(merged_yml, f.yml)
    assert yaml_dump(merged_yml) == snapshot(name='merged.yml')


def test_wc_services(wc_compose_group, snapshot):
    """test the result of get_wc_services"""
    assert list(wc_compose_group.get_wc_services()) == snapshot()
