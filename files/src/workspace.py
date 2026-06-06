import os

from .compose import compose_files_find
from .utils import FatalError, call_process, print_err, yaml_load


def _get_user_services(cfg):
    names = set()
    for f_paths in compose_files_find(cfg, user_only=True).values():
        for f_path in f_paths:
            y = yaml_load(f_path)
            for name, service in y.get('services', {}).items():
                if 'x-web-conductor' in service:
                    if name in names:
                        raise FatalError(f"{name}: duplicate 'x-web-conductor' configuration")
                    names.add(name)
                    yield name, service['x-web-conductor']


def _get_user_repositories(cfg):
    for name, config in _get_user_services(cfg):
        if 'repo' in config:
            yield name, config['repo']


def workspace_update(cfg):
    # run generator to catch any errors
    for name, repo in list(_get_user_repositories(cfg)):
        if 'url' in repo:
            print_err(f"{name}: updating")
            mtime = repo.get('mtime', True)
            call_process([
                './scripts/repo-update.sh',
                name, repo['url'],
            ], env={
                'GIT_MTIME': '1' if mtime else ''
            })
