#!/usr/bin/env -S pipx run --path

# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "pyyaml",
# ]
# ///

import argparse
import os

from src.bash import bash_dump
from src.compose import compose_files_create, compose_files_find
from src.config import Config
from src.utils import call_compose
from src.volume import volume_backup

# TODO: consider using relative paths for compose files
root_dir = os.path.realpath(os.path.dirname(__file__))

os.chdir(root_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='web-conductor')
    parser.add_argument('--sudo', action='store_true', help='use sudo for calling docker-compose')

    subparsers = parser.add_subparsers(title='commands', dest='command')
    subparsers.required = True

    parser_config = subparsers.add_parser('config', description='write final compose file')

    parser_compose = subparsers.add_parser('compose', description='call docker-compose')
    parser_compose.add_argument('args', nargs='*', help='arguments to pass to docker-compose')

    parser_volume = subparsers.add_parser('volume', description='volume operations')
    parser_volume_sub = parser_volume.add_subparsers(title='commands', dest='command_volume')
    parser_volume_sub.required = True

    parser_volume_backup = parser_volume_sub.add_parser('backup', description='volume backup')
    parser_volume_backup.add_argument('name', help='volume name')
    # parser_volume_restore = parser_volume_sub.add_parser('restore', description='volume restore')
    # parser_volume_restore.add_argument('file', help='backup file')

    subparsers.add_parser('bash', description='dump service data for bash processing')

    aliased_compose_cmds = {
        'up': ['up', '-d', '--remove-orphans'],
        'up-build': ['up', '--build', '-d', '--remove-orphans'],
        'up-recreate': ['up', '-d', '--remove-orphans', '--force-recreate'],
        'down': ['down', '--remove-orphans'],
        'logs': ['logs', '-f', '--tail=50'],
        'traefik-reload-dynamic': ['exec', 'traefik', 'touch', '/etc/traefik/dynamic'],
    }

    for cmd in aliased_compose_cmds:
        p = subparsers.add_parser(cmd, description='alias for \'compose %s\'' % (' '.join(aliased_compose_cmds[cmd])))
        p.add_argument('args', nargs='*', help='arguments to pass to docker-compose')

    args = parser.parse_args()
    cfg = Config.load(root_dir)

    if args.command == 'config':
        compose_files_create(cfg)

    if args.command == 'compose':
        call_compose(args.args, ['sudo'] if args.sudo else [])

    if args.command == 'volume':
        if args.command_volume == 'backup':
            if not volume_backup(cfg.root_dir, args.name, args.sudo):
                exit(1)

    if args.command == 'bash':
        compose_files = compose_files_find(cfg)
        if not bash_dump(compose_files):
            exit(1)

    if args.command in aliased_compose_cmds:
        cmd_args = list(aliased_compose_cmds[args.command])
        cmd_args.extend(args.args)
        call_compose(cmd_args, ['sudo'] if args.sudo else [])
