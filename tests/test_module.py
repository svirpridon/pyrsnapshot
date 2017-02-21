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
        pyrs.Snapshot('hourly.23', NOW.shift(hours=-24)),
        pyrs.Snapshot('daily.00', NOW.shift(days=-2)),
        pyrs.Snapshot('daily.05', NOW.shift(days=-8)),
        # We "lost" days.6, so no rotation
        pyrs.Snapshot('weekly.00', NOW.shift(weeks=-2)),
        pyrs.Snapshot('weekly.03', NOW.shift(weeks=-6)),
        pyrs.Snapshot('monthly.00', NOW.shift(months=-2)),
        pyrs.Snapshot('monthly.10', NOW.shift(months=-13)),
        # We "lost" months.11, so no rotation
        pyrs.Snapshot('yearly.0', NOW.shift(years=-2)),
        pyrs.Snapshot('yearly.4', NOW.shift(years=-7)),
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
        dailies = snapshots._filter('daily')
        weeklies = snapshots._filter('weekly')
        # We didn't make up data
        assert_that(self.DATA).contains(*dailies)
        assert_that(self.DATA).contains(*weeklies)
        # No overlap allowed
        assert_that(dailies).does_not_contain(*weeklies)
        assert_that(weeklies).does_not_contain(*dailies)
        # We didn't lose any data
        assert_that(dailies).is_length(2)
        assert_that(weeklies).is_length(2)

    def test_next_frequency(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        first = pyrs.ADJECTIVES[0:-1]
        last = pyrs.ADJECTIVES[1:]
        for small, big in zip(first, last):
            assert_that(snapshots.next_frequency(small)).is_equal_to(big)
        assert_that(snapshots.next_frequency).is_none()

    def test_rotate(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        assert_that(snapshots.should_rotate_up('hourly')).is_true()
        assert_that(snapshots.should_rotate_up('daily')).is_false()
        assert_that(snapshots.should_rotate_up('weekly')).is_true()
        assert_that(snapshots.should_rotate_up('monthly')).is_false()
        assert_that(snapshots.should_rotate_up('yearly')).is_true()
