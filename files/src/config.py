import os

from .utils import print_err, yaml_load


class Config:
    @classmethod
    def load(cls, root_dir):
        file = os.path.join(root_dir, 'config.yml')
        if os.path.isfile(file):
            return cls(root_dir, yaml_load(file))
        # fallback to ansible defaults for local testing
        if os.path.basename(root_dir) == 'files':
            file = os.path.join(os.path.dirname(root_dir), 'defaults', 'main.yml')
        if os.path.isfile(file):
            print_err("WARNING: using ansible defaults as 'config.yml', local testing?")
            return cls(root_dir, yaml_load(file))
        raise RuntimeError("'config.yml' not found")

    def __init__(self, root_dir, y_config):
        self.root_dir = root_dir
        self.user_dir = os.path.join(root_dir, 'user')
        self.wc = {}
        for k, v in y_config.items():
            if k[:3] == 'wc_':
                self.wc[k[3:]] = v

    def get_repo_dir(self, service_name):
        return os.path.join(self.root_dir, 'workspace', 'services', service_name, 'repo')
