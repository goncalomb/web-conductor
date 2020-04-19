#!/usr/bin/python3

import os, re, io, sys, glob, signal, subprocess, argparse, yaml, shlex

dir_root = os.path.realpath(os.path.dirname(__file__))

def find_compose_files():
    files = [f for f in os.listdir(dir_root) if re.match('^docker-compose-\\d{3}.yaml$', f)]
    files.sort()
    return [(f, os.path.join(dir_root, f)) for f in files]

def load_yaml(file):
    with io.open(file, 'r') as fp:
        return yaml.safe_load(fp)

def convert_services_yaml(y):
    y_new = {
        'version': y['version'],
        'services': {}
    }
    services = y.get('services', {})
    if services:
        for s in services:
            if 'web-conductor' in services[s]:
                conductor = services[s]['web-conductor'] or {}
                del services[s]['web-conductor']
                data = {
                    'restart': 'always',
                    'labels': [
                        'traefik.enable=true'
                    ]
                }
                labels = data['labels']
                y_new['services'][s] = data
                if 'repo-host' in conductor and 'repo-name' in conductor:
                    data['build'] = {
                        'context': os.path.join(dir_root, 'workspace', 'services', conductor['repo-name'])
                    }
                    dockerfile = os.path.join(dir_root, 'dockerfiles', s + '.dockerfile')
                    if os.path.isfile(dockerfile):
                        data['build']['dockerfile'] = dockerfile
                if 'host' in conductor:
                    if 'port' in conductor:
                        labels.append('traefik.http.services.%s.loadbalancer.server.port=%s' % (s, conductor['port']))
                    labels.append('traefik.http.routers.%s-http.entryPoints=http' % (s))
                    labels.append('traefik.http.routers.%s-http.rule=Host(`%s`)' % (s, conductor['host']))
                    labels.append('traefik.http.routers.%s-http.middlewares=302https@file' % (s))
                    labels.append('traefik.http.routers.%s-https.entryPoints=https' % (s))
                    labels.append('traefik.http.routers.%s-https.rule=Host(`%s`)' % (s, conductor['host']))
                    labels.append('traefik.http.routers.%s-https.middlewares=302https@file' % (s))
                    labels.append('traefik.http.routers.%s-https.tls' % (s))
    return y_new

def create_composer_files():
    files = []
    for (f, fpath) in find_compose_files():
        y = load_yaml(fpath)
        f_o_path = os.path.join(dir_root, f[:-5] + '-O.web-conductor' + f[-5:])
        f_x_path = os.path.join(dir_root, f[:-5] + '-X.web-conductor' + f[-5:])

        y_new = convert_services_yaml(y)

        files.append(f_o_path)
        with io.open(f_o_path, 'w+') as fp:
            yaml.safe_dump(y, fp, default_flow_style=False)

        if y_new['services']:
            files.append(f_x_path)
            with io.open(f_x_path, 'w+') as fp:
                yaml.safe_dump(y_new, fp, default_flow_style=False)
    return files

def call_process(args):
    def void_handler(*_): pass
    prev_term = signal.getsignal(signal.SIGTERM)
    prev_int = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGTERM, void_handler)
    signal.signal(signal.SIGINT, void_handler)
    subprocess.call(args)
    signal.signal(signal.SIGTERM, prev_term)
    signal.signal(signal.SIGINT, prev_int)

def call_composer(args, args_pre=[], keep_files=False):
    files = create_composer_files()
    all_args = []
    all_args.extend(args_pre)
    all_args.append('docker-compose')
    for f in files:
        all_args.append('-f')
        all_args.append(f)
    all_args.extend(args)
    call_process(all_args)
    if not keep_files:
        for f in files:
            os.unlink(f)

def bash_dump():
    data={}
    for (f, fpath) in find_compose_files():
        y = load_yaml(fpath)
        services = y.get('services', {})
        if services:
            for s in services:
                if 'web-conductor' in services[s]:
                    if s in data:
                        print('[web-conductor] duplicate \'web-conductor\' configuration for service \'%s\'' % (s), file=sys.stderr)
                        return False
                    data[s] = services[s]['web-conductor'] or {}

    data_services = []
    data_repo_hosts = []
    data_repo_names = []
    for s in data:
        data_services.append(s)
        data_repo_hosts.append(str(data[s]['repo-host']) if 'repo-host' in data[s] else "")
        data_repo_names.append(str(data[s]['repo-name']) if 'repo-name' in data[s] else "")
    data_services = map(shlex.quote, data_services)
    data_repo_hosts = map(shlex.quote, data_repo_hosts)
    data_repo_names = map(shlex.quote, data_repo_names)
    print('WC_SERVICES=(%s)' % (' '.join(data_services)))
    print('WC_REPO_HOSTS=(%s)' % (' '.join(data_repo_hosts)))
    print('WC_REPO_NAMES=(%s)' % (' '.join(data_repo_names)))
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='web-conductor')
    parser.add_argument('--sudo', action='store_true', help='use sudo for calling docker-compose')

    subparsers = parser.add_subparsers(title='commands', dest='command')
    subparsers.required = True

    parser_compose = subparsers.add_parser('compose', description='call docker-compose')
    parser_compose.add_argument('args', nargs='*', help='arguments to pass to docker-compose')

    subparsers.add_parser('bash', description='dump service data for bash processing')

    aliased_composer_cmds = {
        'up': ['up', '-d', '--remove-orphans'],
        'down': ['down', '--remove-orphans']
    }

    for cmd in aliased_composer_cmds:
        p = subparsers.add_parser(cmd, description='alias for \'compose %s\'' % (' '.join(aliased_composer_cmds[cmd])))
        p.add_argument('args', nargs='*', help='arguments to pass to docker-compose')

    args = parser.parse_args()

    if args.command == 'compose':
        call_composer(args.args, ['sudo'] if args.sudo else [])

    if args.command == 'bash':
        if not bash_dump():
            exit(1)

    if args.command in aliased_composer_cmds:
        cmd_args = list(aliased_composer_cmds[args.command])
        cmd_args.extend(args.args)
        call_composer(cmd_args, ['sudo'] if args.sudo else [])
