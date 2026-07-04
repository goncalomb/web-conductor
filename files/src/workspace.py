from .compose import compose_files_find
from .utils import FatalError, call_process, print_err


def workspace_update(cfg):
    for config in compose_files_find(cfg, user_only=True).get_wc_services():
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
