# Tasks
#   check remote connectivity
#       you define as who/etc via ~/.ssh/config
#   check remote disk space
#       analyze disk space used for the full, plus space used for the deltas
#   do the sync backup to a temp space
#       don't use the --link-dest=.../hours.0 on first sync
#   do the appropriate remote rotations
#       rotate based on what is found and what we keep
#       --keep "3 months" means
#           Hourly as often as you run it via cron
#           Daily for 7 days
#           Weekly for 4 weeks
#           Monthly for 3 months
#   Rotation:
#       for hours.n -> days.0
#           when delta(hours.n - days.0) > 24
#       for days.6 -> weeks.0
#           when delta(days.6 - weeks.0) > 7
#       for weeks.3 -> months.0
#   How many to keep in each rotation:
#       --hours 24
#       --days 7
#       --weeks 4
#       --months 12
#       --years 4

import arrow
import functools
import os
import re

from fabric.api import *
from fabric.contrib.files import exists
from fabric.contrib.project import rsync_project

LOCAL = '<local-only>'
NOUNS = ['hours', 'days', 'weeks', 'months', 'years']
ADJECTIVES = ['hourly', 'daily', 'weekly', 'monthly', 'yearly']
DEFAULTS = [24, 7, 4, 13, 4]
NOMINALIZE = dict(zip(ADJECTIVES, NOUNS))
NOMINALIZE_PREV = dict(zip(ADJECTIVES, ['minutes'] + NOUNS))
SNAPSHOT = re.compile(r'({})[.]([\d]{{2}})'.format('|'.join(ADJECTIVES)))


@task
def check_disk_space(path):
    with cd(path):
        df = run('df -k .')
        keys, data = df.splitlines()
        return dict(zip(keys.split(), data.split()))

@task
def get_snapshots(path):
    with cd(path):
        ls = run("ls --time-style='+%FT%T.000%z' -otg")
        results = []
        for entry in ls.splitlines():
            if entry.startswith('total'):
                continue
            # Probably a backup directory line
            (*_, timestamp, filename) = entry.split(maxsplit=5)
            matched = SNAPSHOT.match(filename)
            if matched:
                results.append(Snapshot(filename, timestamp))
        return results

@task
def rotate_freq(path, frequency, **kwargs):
    backups = execute(get_snapshots, path)[LOCAL]
    snapshots = Snapshots(*backups, **kwargs)

    next_frequency = snapshots.next_frequency(frequency)

    # Is there anything to do?
    current = snapshots.filter(frequency)
    if snapshots.rotate(frequency) and current[0].filename.endswith('.00'):
        # Do we have too many snapshots and should purge some?
        for entry in snapshots.excess(frequency):
            current.remove(entry)
            run('rm -rf ./{}'.format(entry.filename))

        if snapshots.full(frequency) and next_frequency:
            # We're full but there is a next frequency to roll to
            filename = '{}.00'.format(next_frequency)
            current.append(Snapshot(filename))
        elif not next_frequency:
            # We're full and at the end of the line.
            run('rm -rf ./{}'.format(current[-1].filename))
        else:
            # We're not full, just rotate into the next empty slot
            _, last = current[-1].filename.split('.')
            filename = '{}.{:02d}'.format(frequency, int(last) + 1)
            current.append(Snapshot(filename))

        # Create the src:dst pairs, but do it in reverse order
        pairs = list(zip(current, current[1:]))
        for src, dst in reversed(pairs):
            run('mv {} {}'.format(src.filename, dst.filename))
    elif frequency != ADJECTIVES[0]:
        # Nope, purge the 00 file if we aren't hourly
        temp = '{}.00'.format(frequency)
        if execute(exists, temp)[LOCAL]:
            run('rm -rf ./{}'.format(temp))

    # If there is a next frequency, try to rotate it just in case
    # we died mid-process
    if next_frequency:
        execute(rotate_freq, path, next_frequency, **kwargs)

@task
def rotate(path, args):
    kwargs = {key: getattr(args, key) for key in ADJECTIVES}
    with cd(path):
        execute(rotate_freq, path, ADJECTIVES[0], **kwargs)

@task
def sync(path):
    hourly_first = os.path.join(path, 'hourly.01')
    if not execute(exists, hourly_first)[LOCAL]:
        # Do the first backup
        execute(rsync_project, hourly_first, default_opts='-avz')
    else:
        # Do relative backups
        hourly_wip = os.path.join(path, 'hourly.00')
        cmd = 'touch' if execute(exists, hourly_wip)[LOCAL] else 'mkdir'
        run('{} {}'.format(cmd, hourly_wip))
        execute(
            rsync_project,
            hourly_wip,
            default_opts='-avz',
            extra_opts='--link-dest={}'.format(hourly_first)
        )

@task
def pyrsnapshot(path, args):
    with quiet():
        execute(exists, path)
        #execute(check_disk_space, path)
        execute(sync, path)
        execute(rotate, path, args)


class Snapshots(object):
    '''
    A collection of Snapshot objects to implement rsnapshot-like
    rotation.
    '''

    def __init__(self, *snapshots, hourly=24, daily=7, weekly=4, monthly=12, yearly=5):
        '''
        Create a collection of snapshots to inspect and manipulate
        with the given retention/rotation characteristics.
        '''
        self.hourly = hourly
        self.daily = daily
        self.weekly = weekly
        self.monthly = monthly
        self.yearly = yearly
        self.snapshots = sorted(snapshots)

    def __iter__(self):
        return iter(self.snapshots)

    def __len__(self):
        return len(self.snapshots)

    def __getitem__(self, item):
        return self.snapshots[item]

    def excess(self, frequency):
        return self.filter(frequency)[self.limit(frequency) + 1:]

    def filter(self, frequency):
        return [s for s in self.snapshots if s.frequency == frequency]

    def full(self, frequency):
        return len(self.filter(frequency)) > self.limit(frequency)

    def limit(self, frequency):
        return getattr(self, frequency)

    def next_frequency(self, frequency):
        '''
        Return the next frequency up from the given frequency if
        and only if there are slots available in it.
        '''
        index = ADJECTIVES.index(frequency) + 1
        if index < len(ADJECTIVES):
            future = ADJECTIVES[index]
            if getattr(self, future) > 0:
                return future

    def rotate(self, frequency):
        '''
        Return true if the frequency listed is ready to rotate.
        '''
        snapshots = self.filter(frequency)
        if len(snapshots) >= 2 and snapshots[0].filename.endswith('.00'):
            # Compare the first two snapshots to see if we are ready
            candidate, leader, *_ = self.filter(frequency)
            # Shift less than the full frequency to allow for minor
            # variations in start or run time to still backup every
            # period.
            delta = {
                NOMINALIZE[frequency]: -1,
                NOMINALIZE_PREV[frequency]: +1,
            }
            return candidate.arrow.shift(**delta) >= leader.arrow
        elif len(snapshots) == 1 and snapshots[0].filename.endswith('.00'):
            # Rotate a single snapshot only if it is in the temp spot
            return True
        else:
            return False


@functools.total_ordering
class Snapshot(object):
    @property
    def filename(self):
        return '{}.{}'.format(self.frequency, self.index)

    def __init__(self, filename, timestamp=0):
        self.frequency, self.index = filename.split('.')
        self.arrow = arrow.get(timestamp)

    def __repr__(self):
        fmt = "<Snapshot {0.frequency}.{0.index} at {0.arrow}>"
        return fmt.format(self)

    def __eq__(self, other):
        return (self.frequency == other.frequency and
                self.index == other.index)

    def __lt__(self, other):
        if self.frequency == other.frequency:
            return self.index < other.index
        else:
            return (ADJECTIVES.index(self.frequency) <
                    ADJECTIVES.index(other.frequency))
