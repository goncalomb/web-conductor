import os
import re

from .config import Config
from .labels import HomepageConfig, TraefikConfigGroup, TraefikMiddleware, TraefikRouter, TraefikService
from .models import ComposeFile as ComposeFileModel
from .models import Route, XWebConductorService
from .utils import call_process, yaml_dump_print_changes, yaml_load


def compose_merge(a, b, *, root_x_on_top=True):
    """
    Merge two compose files. This is a normal recursive merge (dicts are merged,
    lists are appended), it does not follow the Docker Compose merge exceptions.
    https://docs.docker.com/reference/compose-file/merge/
    This is only effectively used to merge our x-web-conductor keys in memory,
    the output is not used to generate the final compose.yml file.
    Keys starting with x- on root are moved to the top so that our x- anchors
    look nice for testing (i.e the anchors appear at the top, before the alias).
    """
    if isinstance(a, dict) and isinstance(b, dict):
        a = a.copy()
        for k, v in b.items():
            a[k] = compose_merge(a.get(k), v, root_x_on_top=False)
        if root_x_on_top:
            x = {}
            r = {}
            for k, v in a.items():
                (x if k.startswith('x-') else r)[k] = v
            a = {**x, **r}
        return a
    elif isinstance(a, list) and isinstance(b, list):
        return a + b
    return b


class ComposeFileBase():
    def __init__(self, name: str, yml):
        self.name = name
        self.yml = yml
        self.dat = ComposeFileModel.model_validate(self.yml)

    def _create_traefik_labels(self, cfg: Config, wcs: XWebConductorService):
        base_name = wcs.service_name.replace('.', '-') + '-' + cfg.wc.compose_name
        tcg = TraefikConfigGroup()

        def create_router(name_parts, route: Route, *, entrypoint='https'):
            name = '~'.join(name_parts)
            tr = tcg.add(TraefikRouter(name))

            # entry point (https is set as default on traefik.toml)
            if entrypoint != 'https':
                tr.set('entryPoints', entrypoint)

            # hardcoded service for traefik dashboard
            if wcs.service_name == 'traefik' and route.admin:
                tr.set('service', 'api@internal')

            # rule
            rule = []
            if r_host := route.host or (cfg.wc.traefik_admin_host if route.admin else None):
                rule.append(f'Host(`{r_host}`)')
            if route.path == '/':
                rule.append('PathPrefix(`/`)')
            elif route.path:
                rule.append(f'(Path(`{route.path}`) || PathPrefix(`{route.path}/`))')
            if rule:
                tr.set('rule', ' && '.join(rule))

            # priority
            if route.priority:
                tr.set('priority', route.priority)

            # middlewares
            if route.internal is True or route.internal is None and route.admin and cfg.wc.traefik_admin_use_internal:
                tr.set('middlewares', 'internal@file', append=True)
            if route.auth is True or route.auth is None and route.admin and cfg.wc.traefik_admin_use_auth:
                tr.set('middlewares', 'auth@file', append=True)

            if route.location:
                tm = tcg.add(TraefikMiddleware(name + '+location'))
                tm.set('redirectregex.regex', '^.+$')
                tm.set('redirectregex.replacement', route.location)
                tr.set('middlewares', tm.name, append=True)
                # hardcoded noop@internal service for limbo redirects
                if wcs.service_name == 'limbo':
                    tr.set('service', 'noop@internal')

        # main service route
        if wcs.route:
            if wcs.route.port:
                ts = tcg.add(TraefikService(base_name))
                ts.set('loadbalancer.server.port', wcs.route.port)
            create_router([base_name], wcs.route)

        # extra service routes
        if wcs.routes:
            for name, route in wcs.routes.items():
                # TODO: port
                create_router([base_name, name], route)

        labels = list(tcg.to_labels())
        if labels:
            labels.insert(0, 'traefik.enable=true')
        return labels

    def _create_homepage_labels(self, cfg: Config, wcs: XWebConductorService):
        h = HomepageConfig()
        if wcs.homepage:
            # set basic homepage config
            h.set('group', self.dat.x_web_conductor.group)
            h.set('icon', 'mdi-server-outline')
            h.set('name', wcs.name or wcs.service_name + ' @ ' + self.name)
            if wcs.description:
                h.set('description', wcs.description)
            # set href from route
            if wcs.route:
                if host := wcs.route.host or (cfg.wc.traefik_admin_host if wcs.route.admin else None):
                    h.set('href', f'https://{host}{wcs.route.path or "/"}')
            # set homepage extras
            if isinstance(wcs.homepage, dict):
                for k, v in wcs.homepage.items():
                    h.set(k, v)
        return list(h.to_labels())

    def _create_base_y(self, cfg: Config, rel_to: str):
        y = {
            'x-base': cfg.wc.compose_service_base,
            'services': {}
        }
        for name, service in self.dat.services.items():
            if service.x_web_conductor:
                y['services'][name] = y['x-base']
        return y if y['services'] else None

    def _create_data_y(self, cfg: Config, rel_to: str):
        y = {
            'x-logging': {
                'driver': cfg.wc.compose_logging_driver,
                'options': cfg.wc.compose_logging_options,
            },
            'services': {}
        }
        for name, service in self.dat.services.items():
            if wcs := service.x_web_conductor:
                data = y['services'][name] = {}
                if wcs.repo:
                    data['build'] = {
                        'context': cfg.get_repo_dir(name, rel_to),
                    }
                if name != 'loki':
                    data['depends_on'] = ['loki']
                data['logging'] = y['x-logging']
                data['labels'] = self._create_traefik_labels(cfg, wcs)
                data['labels'] += self._create_homepage_labels(cfg, wcs)
        return y if y['services'] else None

    def create_layers(self, cfg: Config, rel_to: str):
        f_name, f_ext = os.path.splitext(self.name)
        for name, yml in [
            ('base', self._create_base_y(cfg, rel_to)),
            ('data', self._create_data_y(cfg, rel_to)),
        ]:
            if yml:
                yield f_name + '.' + name + f_ext, yml


class ComposeFile(ComposeFileBase):
    def __init__(self, name: str, path: str):
        super().__init__(name, yaml_load(path))
        self.path = path


class ComposeFileGroup():
    def __init__(self, name: str, paths: list[str]):
        self.name = name
        self.files = [ComposeFile(name, path) for path in paths]
        merged_yml = {}
        for f in self.files:
            merged_yml = compose_merge(merged_yml, f.yml)
        self.merged = ComposeFileBase(name, merged_yml)

    def get_wc_services(self):
        for service in self.merged.dat.services.values():
            if service.x_web_conductor:
                yield service.x_web_conductor

    def create_layers(self, cfg: Config, rel_to: str):
        yield from self.merged.create_layers(cfg, rel_to)


class ComposeFileCollection():
    def __init__(self, files: dict[str, list[str]]):
        self.groups = [ComposeFileGroup(name, paths) for name, paths in files.items()]

    def get_wc_services(self):
        for g in self.groups:
            yield from g.get_wc_services()

    def write_result_files(self, cfg: Config):
        def create_layers(g: ComposeFileGroup):
            layers_dir = os.path.dirname(g.files[0].path)
            for name, yml in g.create_layers(cfg, layers_dir):
                f_path = os.path.join(layers_dir, name)
                yaml_dump_print_changes(yml, f_path)
                yield f_path
            for f in g.files:
                yield f.path

        def create_groups(c: ComposeFileCollection):
            for g in c.groups:
                if paths := list(create_layers(g)):
                    yield paths

        # create final compose.yml file
        yaml_dump_print_changes({
            'name': cfg.wc.compose_name,
            'include': [{'path': p} for p in create_groups(self)]
        }, os.path.join(cfg.root_dir, 'compose.yml'))


def compose_files_find(cfg: Config, *, user_only=False):
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
    return ComposeFileCollection(files)


def compose_files_create(cfg: Config):
    compose_files_find(cfg).write_result_files(cfg)


def compose_call(cfg: Config, args: list[str], args_pre: list[str] = []):
    return call_process(
        args_pre + ['docker', 'compose'] + args,
        env={
            'BUILDX_NO_DEFAULT_ATTESTATIONS': '0' if cfg.wc.compose_default_attestations else '1',
        }
    )
