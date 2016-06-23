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
import collections
import functools
import operator


FREQUENCIES = ['hours', 'days', 'weeks', 'months', 'years']

def next_frequency(frequency):
    return FREQUENCIES[FREQUENCIES.index(frequency) + 1]


@functools.total_ordering
class Snapshot(object):
    def __init__(self, frequency='hours', index=0, timestamp=0):
        self.frequency = frequency
        self.index = index
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
            return (FREQUENCIES.index(self.frequency) <
                    FREQUENCIES.index(other.frequency))


class Snapshots(object):
    '''
    A collection of Snapshot objects to implement rsnapshot-like
    rotation.
    '''

    def __init__(self, *snapshots,
                 hours=24, days=7, weeks=4, months=12, years=5):
        '''
        Create a collection of snapshots to inspect and manipulate
        with the given retention/rotation characteristics.
        '''
        self.hours = hours
        self.days = days
        self.weeks = weeks
        self.months = months
        self.years = years
        self.snapshots = sorted(snapshots)

    def __iter__(self):
        return iter(self.snapshots)

    def __len__(self):
        return len(self.snapshots)

    def __getitem__(self, item):
        return self.snapshots[item]

    def _filter(self, frequency):
        return [s for s in self.snapshots if s.frequency == frequency]

    # TODO: Needs a better name
    def should_rotate_up(self, frequency):
        distance = getattr(self, frequency)
        snapshots = self._filter(frequency)
        trigger = snapshots[-1].arrow.replace(**{frequency: +distance})
        return snapshots[0].arrow >= trigger
