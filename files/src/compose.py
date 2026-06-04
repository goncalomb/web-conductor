import os
import re

from .utils import yaml_dump_print_changes, yaml_load


class ComposeFile():
    def __init__(self, name, path, *, cfg):
        self.name = name
        self.path = path
        self._cfg = cfg

    def _traefik_labels_from_route(self, service_name, route):
        labels = []

        def create_router(name, entrypoint, config, tls=False):
            router_config_prefix = 'traefik.http.routers.%s-%s' % (name, entrypoint)

            # entry point
            labels.append('%s.entryPoints=%s' % (router_config_prefix, entrypoint))

            # rule
            rule = []
            if 'host' in config:
                rule.append('Host(`%s`)' % (config['host']))
            if 'path' in config:
                rule.append('(Path(`%s`) || PathPrefix(`%s/`))' % (config['path'], config['path']))
            labels.append('%s.rule=%s' % (router_config_prefix, ' && '.join(rule)))

            # tls
            if tls:
                labels.append('%s.tls' % (router_config_prefix))

            # middlewares
            middlewares = []
            if not tls and ('https-redirect' not in config or config['https-redirect']):
                middlewares.append('302https@file')
            if 'admin' in config and config['admin']:
                middlewares.append('auth@file')
            if tls and 'location' in config and config['location']:
                labels.append('traefik.http.middlewares.%s.redirectregex.regex=.*' % (name))
                labels.append('traefik.http.middlewares.%s.redirectregex.replacement=%s' % (name, config['location']))
                middlewares.append(name)
            if middlewares:
                labels.append('%s.middlewares=%s' % (router_config_prefix, ','.join(middlewares)))

        if 'host' in route or 'path' in route:
            if 'port' in route:
                labels.append('traefik.http.services.%s.loadbalancer.server.port=%s' % (service_name, route['port']))

            if 'admin' in route and route['admin']:
                create_router(service_name, 'traefik', route, True)
            else:
                create_router(service_name, 'http', route)
                create_router(service_name, 'https', route, True)

        if 'redirect' in route:
            for key in route['redirect']:
                create_router(key, 'http', route['redirect'][key])
                create_router(key, 'https', route['redirect'][key], True)

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
                    data['labels'].extend(self._traefik_labels_from_route(s, conductor))
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


def compose_files_find(cfg):
    # files are grouped by name so that user files can extend root files
    re_compose = r'^compose\.\w+\.ya?ml$'
    files = {}
    for d in [cfg.root_dir, cfg.user_dir]:
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
