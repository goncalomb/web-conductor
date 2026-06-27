import os
import re

from .labels import HomepageConfig, TraefikConfigGroup, TraefikMiddleware, TraefikRouter, TraefikService
from .utils import yaml_dump_print_changes, yaml_load


class ComposeFile():
    def __init__(self, name, path, *, cfg):
        self.name = name
        self.path = path
        self._cfg = cfg
        self._y = yaml_load(path)
        wc = self._y.get('x-web-conductor', {})
        # TODO: better group defaults (we should detect user files)
        # self._wc_group = wc.get('group', '.'.join(self.name.split('.')[1:-1]))
        self._wc_group = wc.get('group', 'User Services')

    def _create_traefik_labels(self, service_name, config):
        base_name = service_name.replace('.', '-') + '-' + self._cfg.wc['compose_name']
        tcg = TraefikConfigGroup()

        def create_router(name_parts, config, *, entrypoint='https'):
            name = '~'.join(name_parts)
            tr = tcg.add(TraefikRouter(name))
            r_admin = config.get('admin', False)

            # entry point (https is set as default on traefik.toml)
            if entrypoint != 'https':
                tr.set('entryPoints', entrypoint)

            # hardcoded service for traefik dashboard
            if service_name == 'traefik' and r_admin:
                tr.set('service', 'api@internal')

            # rule
            rule = []
            if r_host := config.get('host', self._cfg.wc['traefik_admin_host'] if r_admin else None):
                rule.append('Host(`%s`)' % (r_host))
            if r_path := config.get('path', None):
                if r_path == '/':
                    rule.append('PathPrefix(`/`)')
                else:
                    rule.append('(Path(`%s`) || PathPrefix(`%s/`))' % (r_path, r_path))
            if rule:
                tr.set('rule', ' && '.join(rule))

            # priority
            if 'priority' in config:
                tr.set('priority', config['priority'])

            # middlewares
            if config.get('internal', r_admin and self._cfg.wc['traefik_admin_use_internal']):
                tr.set('middlewares', 'internal@file', append=True)
            if config.get('auth', r_admin and self._cfg.wc['traefik_admin_use_auth']):
                tr.set('middlewares', 'auth@file', append=True)

            if location := config.get('location', None):
                tm = tcg.add(TraefikMiddleware(name + '+location'))
                tm.set('redirectregex.regex', '^.+$')
                tm.set('redirectregex.replacement', location)
                tr.set('middlewares', tm.name, append=True)
                # hardcoded noop@internal service for limbo redirects
                if service_name == 'limbo':
                    tr.set('service', 'noop@internal')

        # main service route
        if route := config.get('route', None):
            if 'port' in route:
                ts = tcg.add(TraefikService(base_name))
                ts.set('loadbalancer.server.port', route['port'])
            create_router([base_name], route)

        # extra service routes
        if routes := config.get('routes', None):
            for key in routes:
                create_router([base_name, key], routes[key])

        labels = list(tcg.to_labels())
        if labels:
            labels.insert(0, 'traefik.enable=true')
        return labels

    def _create_homepage_labels(self, service_name, config):
        h = HomepageConfig()
        if homepage := config.get('homepage', False):
            # set basic homepage config
            h.set('group', self._wc_group)
            h.set('icon', 'mdi-server-outline')
            h.set('name', config.get('name', service_name + ' @ ' + self.name))
            if 'description' in config:
                h.set('description', config['description'])
            # set href from route
            if route := config.get('route', {}):
                host = route.get('host', self._cfg.wc['traefik_admin_host'] if route.get('admin', False) else None)
                if host:
                    h.set('href', 'https://%s%s' % (host, route.get('path', '/')))
            # set homepage extras
            if isinstance(homepage, dict):
                for k, v in homepage.items():
                    h.set(k, v)
        return list(h.to_labels())

    def _create_base_y(self):
        y = {
            'x-base': self._cfg.wc['compose_service_base'],
            'services': {}
        }
        for name, service in self._y.get('services', {}).items():
            if 'x-web-conductor' in service:
                y['services'][name] = y['x-base']
        return y if y['services'] else None

    def _create_data_y(self):
        y = {
            'x-logging': {
                'driver': self._cfg.wc['compose_logging_driver'],
                'options': self._cfg.wc['compose_logging_options'],
            },
            'services': {}
        }
        for name, service in self._y.get('services', {}).items():
            if conductor := service.get('x-web-conductor', {}):
                data = y['services'][name] = {}
                if 'repo' in conductor:
                    data['build'] = {
                        'context': self._cfg.get_repo_dir(name, os.path.dirname(self.path)),
                    }
                if name != 'loki':
                    data['depends_on'] = ['loki']
                data['logging'] = y['x-logging']
                data['labels'] = self._create_traefik_labels(name, conductor)
                data['labels'] += self._create_homepage_labels(name, conductor)
        return y if y['services'] else None

    def create_merge_files(self, *, dir=None):
        f_name, f_ext = os.path.splitext(self.name)
        for name, y in [
            ('base', self._create_base_y()),
            ('data', self._create_data_y()),
        ]:
            if y:
                f_path = os.path.join(dir or os.path.dirname(self.path), f_name + '.' + name + f_ext)
                yaml_dump_print_changes(f_path, y)
                yield f_path
        yield self.path


class ComposeFileGroup():
    def __init__(self, name, paths, *, cfg):
        self.name = name
        self.files = [ComposeFile(name, path, cfg=cfg) for path in paths]

    def create_merge_files(self):
        for f in self.files:
            yield from f.create_merge_files()


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
    all_groups = []
    for f, f_paths in compose_files_find(cfg).items():
        cg = ComposeFileGroup(f, f_paths, cfg=cfg)
        f_group = list(cg.create_merge_files())
        if f_group:
            all_groups.append(f_group)

    # create final compose.yml file
    yaml_dump_print_changes(os.path.join(cfg.root_dir, 'compose.yml'), {
        'name': cfg.wc['compose_name'],
        'include': [{'path': g} for g in all_groups]
    })
