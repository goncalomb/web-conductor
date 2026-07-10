import os
from dataclasses import dataclass
from typing import Any, Generator, Iterable

from publicsuffixlist import PublicSuffixList

from .compose import ComposeFileCollection
from .config import Config
from .utils import call_process_sudo


@dataclass
class _DomainTreeNode:
    label: str
    nodes: dict[str, '_DomainTreeNode']
    match: bool = False

    def add_part(self, label):
        if label not in self.nodes:
            self.nodes[label] = _DomainTreeNode(label, {}, False)
        return self.nodes[label]

    def add_parts(self, parts):
        node = self
        for part in parts:
            node = node.add_part(part)
        return node

    def collect(self, generate_wildcards=False, suffix='', skip=False) -> Generator[str, Any, None]:
        name = f'{self.label}.{suffix}' if suffix else self.label
        if self.match and not skip:
            yield name
        if wildcard := generate_wildcards and sum(node.match for node in self.nodes.values()) > 1:
            yield f'*.{name}'
        for label in sorted(self.nodes.keys()):
            node = self.nodes[label]
            yield from node.collect(generate_wildcards, name, wildcard)

    def collect_groups(self, generate_wildcards=False):
        for label in sorted(self.nodes.keys()):
            node = self.nodes[label]
            yield label, list(node.collect(generate_wildcards))


def certs_process_domains(domains: Iterable[str], *, generate_wildcards=True):
    psl = PublicSuffixList()
    root = _DomainTreeNode('', {}, False)
    for domain in domains:
        root.add_parts(reversed(psl.privateparts(domain))).match = True
    return list(root.collect_groups(generate_wildcards))


def certs_list_domains(cfg: Config, cfc: ComposeFileCollection):
    def valid(domain: str):
        for suffix in ['localhost', 'internal']:
            if domain == suffix or domain.endswith(f'.{suffix}'):
                return False
        return True
    return certs_process_domains(
        filter(valid, cfc.get_wc_hosts(cfg)),
        generate_wildcards=cfg.wc.certs_generate_wildcards,
    )


def certbot_cert_exists(cert_name: str):
    return os.path.isdir(f'/etc/letsencrypt/live/{cert_name}')


def certbot_certonly(cfg: Config, domains: list[str], *, staging=False, cert_name=None, extra_args=None):
    args = [
        'certbot', 'certonly',
        '--non-interactive',
        '--agree-tos',
        '--email', cfg.wc.certbot_email,
        '--no-eff-email',
    ]
    if staging:
        args.append('--staging')
    if cert_name:
        args.extend(('--cert-name', cert_name))
    for domain in domains:
        args.extend(('-d', domain))
    if extra_args:
        args.extend(extra_args)
    return call_process_sudo(args)


def certbot_renew(cfg: Config):
    return call_process_sudo([
        'certbot', 'renew',
        '--non-interactive',
    ])


def certbot_certificates(cfg: Config):
    return call_process_sudo([
        'certbot', 'certificates',
        '--non-interactive',
    ])
