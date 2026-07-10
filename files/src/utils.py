import os
import signal
import subprocess
import sys
from typing import overload

import yaml


class FatalError(RuntimeError):
    def __init__(self, *args, exit_code=1):
        super().__init__(*args)
        self.exit_code = exit_code

    def exit(self):
        print_err(self)
        exit(self.exit_code)


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def venv_find_dir(name='.venv'):
    if 'VIRTUAL_ENV' in os.environ:
        return os.environ['VIRTUAL_ENV']
    if sys.executable:
        parts = sys.executable.split(os.sep)
        for i in range(0, len(parts) - 1):
            if parts[i] == name and parts[i + 1] == 'bin':
                return os.sep.join(parts[:i + 1])
    return ''


def yaml_load(file):
    with open(file, 'r') as fp:
        return yaml.safe_load(fp)


@overload
def yaml_dump(data, file: None = None) -> str: ...
@overload
def yaml_dump(data, file: str) -> None: ...


def yaml_dump(data, file: str | None = None):
    if file is None:
        return yaml.safe_dump(data, default_flow_style=False, sort_keys=False)
    with open(file, 'w') as fp:
        return yaml.safe_dump(data, fp, default_flow_style=False, sort_keys=False)


def yaml_dump_check_changes(data, file: str):
    if os.path.isfile(file):
        data_y = yaml_dump(data)
        with open(file, 'r+') as fp:
            data_f = fp.read()
            if data_y == data_f:
                return False
            fp.seek(0)
            fp.truncate()
            fp.write(data_y)
        return True
    yaml_dump(data, file)
    return True


def yaml_dump_print_changes(data, file: str):
    if yaml_dump_check_changes(data, file):
        print(file)


def call_process(*args, **kwargs):
    def void_handler(*_): pass
    prev_term = signal.getsignal(signal.SIGTERM)
    prev_int = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGTERM, void_handler)
    signal.signal(signal.SIGINT, void_handler)
    try:
        return subprocess.call(*args, **kwargs)
    finally:
        signal.signal(signal.SIGTERM, prev_term)
        signal.signal(signal.SIGINT, prev_int)


def call_process_sudo(cmd_args, *args, **kwargs):
    return call_process(
        ['sudo', '--preserve-env=PATH', 'env', '--', *cmd_args],
        *args, **kwargs,
    )
