
from .compose import compose_files_find
from .models import ComposeFile
from .utils import FatalError, call_process, print_err, yaml_load


def _get_user_services(cfg):
    names = set()
    for f_paths in compose_files_find(cfg, user_only=True).values():
        for f_path in f_paths:
            dat = ComposeFile.model_validate(yaml_load(f_path))
            for name, service in dat.services.items():
                if service.x_web_conductor:
                    if name in names:
                        raise FatalError(f"{name}: duplicate 'x-web-conductor' configuration")
                    names.add(name)
                    yield service.x_web_conductor


def workspace_update(cfg):
    # run generator to catch any errors
    for config in list(_get_user_services(cfg)):
        if config.repo:
            print_err(f"{config.service_name}: updating")
            status = call_process([
                './scripts/repo-update.sh',
                config.service_name, config.repo.url,
            ], env={
                'GIT_MTIME': '1' if config.repo.mtime else ''
            })
            if status != 0:
                raise FatalError(f"{config.service_name}: failed to update repository")
