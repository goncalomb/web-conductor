import argparse
import os

from .compose import compose_call, compose_files_create
from .config import Config
from .utils import FatalError, venv_find_dir
from .volume import volume_backup
from .workspace import workspace_update


def main():
    venv_dir = venv_find_dir()
    root_dir = os.path.dirname(venv_dir) if venv_dir else os.getcwd()

    os.chdir(root_dir)

    parser = argparse.ArgumentParser(prog='web-conductor')
    parser.add_argument('--sudo', action='store_true', help='use sudo for calling docker-compose')

    subparsers = parser.add_subparsers(title='commands', dest='command', required=True)

    parser_run = subparsers.add_parser('run', description='run internal commands')
    parser_run_sub = parser_run.add_subparsers(title='commands', dest='command_run', required=True)

    parser_run_sub.add_parser('config', description='write final compose file')
    parser_run_sub.add_parser('update', description='update workspace repositories')

    parser_compose = subparsers.add_parser('compose', description='call docker-compose')
    parser_compose.add_argument('args', nargs='*', help='arguments to pass to docker-compose')

    parser_volume = subparsers.add_parser('volume', description='volume operations')
    parser_volume_sub = parser_volume.add_subparsers(title='commands', dest='command_volume', required=True)

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

    if args.command == 'run':
        if args.command_run == 'config':
            compose_files_create(cfg)
        if args.command_run == 'update':
            workspace_update(cfg)

    if args.command == 'compose':
        compose_call(cfg, args.args, ['sudo'] if args.sudo else [])

    if args.command == 'volume':
        if args.command_volume == 'backup':
            if not volume_backup(cfg.root_dir, args.name, args.sudo):
                exit(1)

    if args.command in aliased_compose_cmds:
        cmd_args = list(aliased_compose_cmds[args.command])
        cmd_args.extend(args.args)
        compose_call(cfg, cmd_args, ['sudo'] if args.sudo else [])


if __name__ == '__main__':
    try:
        main()
    except FatalError as e:
        e.exit()
