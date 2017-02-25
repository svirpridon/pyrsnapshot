import arrow
from assertpy import assert_that
import pyrsnapshot as pyrs
import random
import unittest

class TestSnapshots(unittest.TestCase):
    # Ordered snapshots, small to large, with a striped rotation pattern
    # ie: hours should rotate to days, days should not to weeks,
    #     weeks should to months, months should not to years.
    NOW = arrow.utcnow()
    DATA = (
        pyrs.Snapshot('hourly.00', NOW),
        pyrs.Snapshot('hourly.01', NOW.shift(hours=-1)),
        pyrs.Snapshot('hourly.02', NOW.shift(hours=-2)),
        pyrs.Snapshot('hourly.03', NOW.shift(hours=-3)),
        pyrs.Snapshot('hourly.04', NOW.shift(hours=-4)),
        pyrs.Snapshot('hourly.05', NOW.shift(hours=-5)),
        pyrs.Snapshot('hourly.06', NOW.shift(hours=-6)),
        pyrs.Snapshot('hourly.07', NOW.shift(hours=-7)),
        pyrs.Snapshot('hourly.08', NOW.shift(hours=-8)),
        pyrs.Snapshot('hourly.09', NOW.shift(hours=-9)),
        pyrs.Snapshot('hourly.10', NOW.shift(hours=-10)),
        pyrs.Snapshot('hourly.11', NOW.shift(hours=-11)),
        pyrs.Snapshot('hourly.12', NOW.shift(hours=-12)),
        pyrs.Snapshot('hourly.13', NOW.shift(hours=-13)),
        pyrs.Snapshot('hourly.14', NOW.shift(hours=-14)),
        pyrs.Snapshot('hourly.15', NOW.shift(hours=-15)),
        pyrs.Snapshot('hourly.16', NOW.shift(hours=-16)),
        pyrs.Snapshot('hourly.17', NOW.shift(hours=-17)),
        pyrs.Snapshot('hourly.18', NOW.shift(hours=-18)),
        pyrs.Snapshot('hourly.19', NOW.shift(hours=-19)),
        pyrs.Snapshot('hourly.20', NOW.shift(hours=-20)),
        pyrs.Snapshot('hourly.21', NOW.shift(hours=-21)),
        pyrs.Snapshot('hourly.22', NOW.shift(hours=-22)),
        pyrs.Snapshot('hourly.23', NOW.shift(hours=-23)),
        # Daily is full but with no 00 won't rotate
        pyrs.Snapshot('daily.01', NOW.shift(days=-1)),
        pyrs.Snapshot('daily.02', NOW.shift(days=-2)),
        pyrs.Snapshot('daily.03', NOW.shift(days=-3)),
        pyrs.Snapshot('daily.04', NOW.shift(days=-4)),
        pyrs.Snapshot('daily.05', NOW.shift(days=-5)),
        pyrs.Snapshot('daily.06', NOW.shift(days=-6)),
        pyrs.Snapshot('daily.07', NOW.shift(days=-7)),
        # Single snapshots rotate if they are 00 always
        pyrs.Snapshot('weekly.00', NOW.shift(weeks=-2)),
        pyrs.Snapshot('monthly.01', NOW.shift(months=-1)),
    )

    def test_sorting(self):
        shuffled = list(self.DATA)[:]
        random.shuffle(shuffled)
        # Fix the slight chance shuffle didn't change the ordering.
        if shuffled == self.DATA:
            shuffled.reverse()

        snapshots = pyrs.Snapshots(*shuffled)
        assert_that(tuple(snapshots)).is_equal_to(self.DATA)

    def test_filter(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        dailies = snapshots.filter('daily')
        weeklies = snapshots.filter('weekly')
        # We didn't make up data
        assert_that(self.DATA).contains(*dailies)
        assert_that(self.DATA).contains(*weeklies)
        # No overlap allowed
        assert_that(dailies).does_not_contain(*weeklies)
        assert_that(weeklies).does_not_contain(*dailies)
        # We didn't lose any data
        assert_that(dailies).is_length(7)
        assert_that(weeklies).is_length(1)

    def test_next_frequency(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        periods = pyrs.remote.ADJECTIVES
        for small, big in zip(periods, periods[1:]):
            assert_that(snapshots.next_frequency(small)).is_equal_to(big)
        assert_that(snapshots.next_frequency(big)).is_none()

    def test_rotate(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        assert_that(snapshots.rotate('hourly')).is_true()
        assert_that(snapshots.rotate('daily')).is_false()
        assert_that(snapshots.rotate('weekly')).is_true()
        assert_that(snapshots.rotate('monthly')).is_false()
