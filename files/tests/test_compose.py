import os

from web_conductor.compose import compose_merge
from web_conductor.utils import yaml_dump


def test_files(wc_config, wc_compose_collection, snapshot):
    """test the compose file layers and the final merged result"""
    for g in wc_compose_collection.groups:
        merged_yml = {}
        # generated layers
        for name, yml in g.create_layers(wc_config, os.path.dirname(g.files[0].path)):
            assert yaml_dump(yml) == snapshot(name=name)
            merged_yml = compose_merge(merged_yml, yml)
        # original files
        for i, f in enumerate(g.files):
            assert yaml_dump(f.yml) == snapshot(name=f'{os.path.basename(f.path)}.{i}')
            merged_yml = compose_merge(merged_yml, f.yml)
        # merged result, this approximates the final config that would be
        # created by docker compose (i.e. 'docker compose config')
        assert yaml_dump(merged_yml) == snapshot(name=f'{g.name}_merged.yml')


def test_wc_services(wc_compose_collection, snapshot):
    """test the result of get_wc_services"""
    assert list(wc_compose_collection.get_wc_services()) == snapshot()


def test_wc_hosts(wc_config, wc_compose_collection, snapshot):
    """test the result of get_wc_hosts"""
    assert list(wc_compose_collection.get_wc_hosts(wc_config)) == snapshot()
