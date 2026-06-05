class TraefikConfig:
    def __init__(self, prefix=[]):
        self._data = {}
        self._prefix = prefix

    @property
    def name(self):
        return self._prefix[-1]

    def set(self, key, value, append=False):
        v = self._data
        keys = key.split('.')
        for k in keys[:-1]:
            if k not in v:
                v[k] = {}
            v = v[k]
        k_last = keys[-1]
        if append and k_last in v:
            p = v[k_last]
            if not isinstance(p, list):
                v[k_last] = [p, value]
            else:
                v[k_last] += value
        else:
            v[k_last] = value

    def to_labels(self):
        def _to_labels(d, prefix):
            for k, v in d.items():
                path = prefix + [k]
                if isinstance(v, dict):
                    yield from _to_labels(v, path)
                elif v == '':
                    yield '.'.join(path)
                else:
                    yield '%s=%s' % ('.'.join(path), ','.join(v) if isinstance(v, list) else v)
        yield from _to_labels(self._data, self._prefix)


class TraefikConfigGroup():
    def __init__(self):
        self._lst = []

    def add(self, config):
        self._lst.append(config)
        return config

    def to_labels(self):
        for c in self._lst:
            yield from c.to_labels()


class TraefikService(TraefikConfig):
    def __init__(self, name):
        super().__init__(prefix=['traefik', 'http', 'services', name])


class TraefikRouter(TraefikConfig):
    def __init__(self, name):
        super().__init__(prefix=['traefik', 'http', 'routers', name])


class TraefikMiddleware(TraefikConfig):
    def __init__(self, name):
        super().__init__(prefix=['traefik', 'http', 'middlewares', name])
