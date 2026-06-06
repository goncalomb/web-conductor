import os
import signal
import subprocess
import sys

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


def yaml_load(file):
    with open(file, 'r') as fp:
        return yaml.safe_load(fp)


def yaml_dump(file, data, check_changes=False):
    if check_changes and os.path.isfile(file):
        data_y = yaml.safe_dump(data, default_flow_style=False)
        with open(file, 'r+') as fp:
            data_f = fp.read()
            if data_y == data_f:
                return False
            fp.seek(0)
            fp.truncate()
            fp.write(data_y)
        return True
    with open(file, 'w') as fp:
        yaml.safe_dump(data, fp, default_flow_style=False)
    return True


def yaml_dump_print_changes(file, data):
    if yaml_dump(file, data, True):
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


def call_compose(args, args_pre=[]):
    return call_process(args_pre + ['docker', 'compose'] + args)
