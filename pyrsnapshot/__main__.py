import argparse

from fabric.api import env, execute, quiet
from fabric.network import disconnect_all

from . import remote

def main():
    parser = argparse.ArgumentParser(
        prog='pyrsnapshot',
        description='''\
    Pyrsnapshot will back up the contents of the current directory to the
    remote server and save it under the path given. Use the executing user's
    .ssh/ssh_config to configure the user and private key for the connection.
    ''',
    )
    help = 'Keep how many {} backups (default: {})'
    for adjective, default in zip(remote.ADJECTIVES, remote.DEFAULTS):
        parser.add_argument(
            '--{}'.format(adjective),
            type=int,
            default=default,
            help=help.format(adjective, default)
        )
    parser.add_argument(
        'remote',
        metavar='host:path',
        help='Backup to the remote host at the given path'
    )

    try:
        args = parser.parse_args()
        host, root = args.remote.split(':')
        if not root:
            raise Exception("You must specify the remote path to backup to.")
        with quiet():
            env.use_ssh_config = True
            execute(remote.pyrsnapshot, root, args, hosts=[host])
    finally:
        disconnect_all()

if __name__ == '__main__':
    main()
