import shlex
import sys

from .utils import yaml_load


def bash_array(name, values):
    def bash_v(v):
        return shlex.quote(('1' if v else '') if isinstance(v, bool) else str(v))
    print('declare -a %s=(%s)' % (name, ' '.join(map(bash_v, values))))


def bash_dump(compose_files):
    data = {}
    for fpath in (f for g in compose_files.values() for f in g):
        y = yaml_load(fpath)
        services = y.get('services', {})
        if services:
            for s in services:
                if 'x-web-conductor' in services[s]:
                    if s in data:
                        print('[web-conductor] duplicate \'x-web-conductor\' configuration for service \'%s\'' %
                              (s), file=sys.stderr)
                        return False
                    data[s] = services[s]['x-web-conductor'] or {}

    default_values = {
        'repo_url': '',
        'repo_build': '',
        'repo_mtime': True,
    }
    bash_array('WC_SERVICE_NAME', data.keys())
    for k, v in default_values.items():
        def get_val(d):
            for p in k.split('_'):
                if p not in d:
                    return v
                d = d[p]
            return d
        bash_array('WC_' + k.upper(), [get_val(d) for d in data.values()])
