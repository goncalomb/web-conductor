import os
import re

from .traefik import TraefikConfigGroup, TraefikMiddleware, TraefikRouter, TraefikService
from .utils import yaml_dump_print_changes, yaml_load


class ComposeFile():
    def __init__(self, name, path, *, cfg):
        self.name = name
        self.path = path
        self._cfg = cfg

    def _create_traefik_labels(self, service_name, config):
        base_name = service_name.replace('.', '-') + '-' + self._cfg.wc['name']
        tcg = TraefikConfigGroup()

        def create_router(name_parts, config, *, entrypoint='https'):
            name = '|'.join(name_parts)
            tr = tcg.add(TraefikRouter(name))

            # entry point (https is set as default on traefik.toml)
            if entrypoint != 'https':
                tr.set('entryPoints', entrypoint)

            # hardcoded service for traefik dashboard
            if service_name == 'traefik' and 'admin' in config and config['admin']:
                tr.set('service', 'api@internal')

            # rule
            rule = []
            if 'host' in config:
                rule.append('Host(`%s`)' % (config['host']))
            elif 'admin' in config and config['admin']:
                rule.append('Host(`%s`)' % (self._cfg.wc['admin_host']))
            if 'path' in config:
                if config['path'] == '/':
                    rule.append('PathPrefix(`/`)')
                else:
                    rule.append('(Path(`%s`) || PathPrefix(`%s/`))' % (config['path'], config['path']))
            if rule:
                tr.set('rule', ' && '.join(rule))

            # priority
            if 'priority' in config:
                tr.set('priority', config['priority'])

            # middlewares
            if 'admin' in config and config['admin']:
                tr.set('middlewares', 'auth@file', append=True)
            if 'location' in config and config['location']:
                tm = tcg.add(TraefikMiddleware(name + '~location'))
                tm.set('redirectregex.regex', '^.+$')
                tm.set('redirectregex.replacement', config['location'])
                tr.set('middlewares', tm.name, append=True)

        if 'route' in config:
            route = config['route']
            if 'port' in route:
                ts = tcg.add(TraefikService(base_name))
                ts.set('loadbalancer.server.port', route['port'])

            # XXX: no longer using another entrypoint for admin routes
            # if 'admin' in route and route['admin']:
            #     create_router([base_name], route, entrypoint='traefik')
            # else:
            #     create_router([base_name], route)
            create_router([base_name], route)

        if 'routes' in config:
            for key in config['routes']:
                create_router([base_name, key], config['routes'][key])

        labels = list(tcg.to_labels())
        if labels:
            labels.insert(0, 'traefik.enable=true')
        return labels

    def _create_override(self, y):
        y_new = {
            'services': {}
        }
        services = y.get('services', {})
        if services:
            for s in services:
                if 'x-web-conductor' in services[s]:
                    conductor = services[s]['x-web-conductor'] or {}
                    data = {
                        'restart': 'always',
                        'labels': []
                    }
                    y_new['services'][s] = data
                    if 'repo' in conductor:
                        data['build'] = {
                            'context': self._cfg.get_repo_dir(s),
                        }
                    data['labels'].extend(self._create_traefik_labels(s, conductor))
        return y_new

    def create_override_file(self):
        y = yaml_load(self.path)
        if not y:
            return None
        f_name, f_ext = os.path.splitext(self.name)
        f_path = os.path.join(os.path.dirname(self.path), f_name + '.override' + f_ext)
        y_new = self._create_override(y)
        yaml_dump_print_changes(f_path, y_new)
        return f_path


class ComposeFileGroup():
    def __init__(self, name, paths, *, cfg):
        self.name = name
        self.files = [ComposeFile(name, path, cfg=cfg) for path in paths]

    def create_override_files(self):
        for f in self.files:
            f_override = f.create_override_file()
            if f_override:
                yield f.path, f_override


def compose_files_find(cfg, *, user_only=False):
    # files are grouped by name so that user files can extend root files
    re_compose = r'^compose\.\w+\.ya?ml$'
    files = {}
    for d in [cfg.root_dir, cfg.user_dir] if not user_only else [cfg.user_dir]:
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if re.match(re_compose, f):
                if f in files:
                    files[f].append(os.path.join(d, f))
                else:
                    files[f] = [os.path.join(d, f)]
    return files


def compose_files_create(cfg):
    # create override files
    all_groups = []
    for f, f_paths in compose_files_find(cfg).items():
        f_group = []
        cg = ComposeFileGroup(f, f_paths, cfg=cfg)
        for final_paths in cg.create_override_files():
            f_group.extend(final_paths)
        if f_group:
            all_groups.append(f_group)

    # create final compose.yml file
    yaml_dump_print_changes(os.path.join(cfg.root_dir, 'compose.yml'), {
        'name': cfg.wc['name'],
        'include': [{'path': g} for g in all_groups]
    })
