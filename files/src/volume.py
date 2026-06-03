import os
import subprocess
import tempfile
import time

from .utils import call_process


def volume_inspect(name, use_sudo=False):
    args = ['sudo'] if use_sudo else []
    args.extend(['docker', 'volume', 'inspect', name])
    print('inspecting volume \'%s\'...' % (name))
    return call_process(args, stdout=subprocess.DEVNULL) == 0


def volume_backup(dir_root, name, use_sudo=False):
    if not volume_inspect(name, use_sudo):
        return False

    dir_backup = os.path.join(dir_root, 'backups', 'volumes')
    os.makedirs(dir_backup, exist_ok=True)

    fd, tmp_file = tempfile.mkstemp(suffix='.tar.gz', dir=dir_backup)
    os.close(fd)

    print('creating backup...')
    args = ['sudo'] if use_sudo else []
    args.extend([
        'docker', 'run', '--init', '--rm',
        '-v', '%s:/tmp/volume:ro' % (name),
        '-v', '%s:/tmp/file' % (tmp_file),
        'busybox', 'tar', '-f', '/tmp/file', '-czC', '/tmp', 'volume'
    ])
    ret = call_process(args)

    if ret != 0:
        print("docker exited with non-zero status code (%s), aborting..." % (ret))
        os.unlink(tmp_file)
        return False

    final_name = '%s_%s.tar.gz' % (name, str(int(time.time())))
    print('saved to \'%s\'' % (final_name))
    os.rename(tmp_file, os.path.join(dir_backup, final_name))
    return True
