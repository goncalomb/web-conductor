import shlex
import sys

from .utils import yaml_load


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

    data_services = []
    data_repo_hosts = []
    data_repo_names = []
    data_build_cmds = []
    for s in data:
        data_services.append(s)
        data_repo_hosts.append(str(data[s]['repo-host']) if 'repo-host' in data[s] else "")
        data_repo_names.append(str(data[s]['repo-name']) if 'repo-name' in data[s] else "")
        data_build_cmds.append(str(data[s]['build']) if 'build' in data[s] else "")
    data_services = map(shlex.quote, data_services)
    data_services = map(shlex.quote, data_services)
    data_repo_hosts = map(shlex.quote, data_repo_hosts)
    data_repo_names = map(shlex.quote, data_repo_names)
    data_build_cmds = map(shlex.quote, data_build_cmds)
    print('WC_SERVICES=(%s)' % (' '.join(data_services)))
    print('WC_REPO_HOSTS=(%s)' % (' '.join(data_repo_hosts)))
    print('WC_REPO_NAMES=(%s)' % (' '.join(data_repo_names)))
    print('WC_BUILD_CMDS=(%s)' % (' '.join(data_build_cmds)))
    return True
