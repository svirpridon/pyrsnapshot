import argparse

from fabric.api import execute
from fabric.network import disconnect_all

from . import remote

parser = argparse.ArgumentParser(prog='pyrsnapshot', description='Simple remote rsync backup')
parser.add_argument('--hourly', type=int, default=24, help='Keep how many hourly backups')
parser.add_argument('--daily', type=int, default=7, help='Keep how many daily backups')
parser.add_argument('--weekly', type=int, default=4, help='Keep how many weekly backups')
parser.add_argument('--monthly', type=int, default=13, help='Keep how many monthly backups')
parser.add_argument('--yearly', type=int, default=4, help='Keep how many yearly backups')
parser.add_argument('remote', help='Remote host:path to backup against')

if __name__ == '__main__':
    try:
        args = parser.parse_args()
        host, root = args.remote.split(':')
        result = execute(remote.pyrsnapshot, root, args, hosts=[host])
    finally:
        disconnect_all()
