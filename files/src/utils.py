import io
import signal
import subprocess

import yaml


def yaml_load(file):
    with io.open(file, 'r') as fp:
        return yaml.safe_load(fp)


def yaml_dump(file, data):
    with io.open(file, 'w') as fp:
        yaml.safe_dump(data, fp, default_flow_style=False)


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
