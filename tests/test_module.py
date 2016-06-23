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
        pyrs.Snapshot('hours',  -1, NOW),
        pyrs.Snapshot('hours',   0, NOW.replace(hours=-1)),
        pyrs.Snapshot('hours',   1, NOW.replace(hours=-2)),
        pyrs.Snapshot('hours',  23, NOW.replace(hours=-24)),
        pyrs.Snapshot('days',    0, NOW.replace(days=-2)),
        pyrs.Snapshot('days',    5, NOW.replace(days=-8)),
        # We "lost" days.6, so no rotation
        pyrs.Snapshot('weeks',   0, NOW.replace(weeks=-2)),
        pyrs.Snapshot('weeks',   3, NOW.replace(weeks=-6)),
        pyrs.Snapshot('months',  0, NOW.replace(months=-2)),
        pyrs.Snapshot('months', 10, NOW.replace(months=-13)),
        # We "lost" months.11, so no rotation
        pyrs.Snapshot('years',   0, NOW.replace(years=-2)),
        pyrs.Snapshot('years',   4, NOW.replace(years=-7)),
    )

    def test_sorting(self):
        shuffled = list(self.DATA)[:]
        random.shuffle(shuffled)
        # Fix the 1-in-many it was actually ordered right.
        if shuffled == self.DATA:
            shuffled.reverse()

        snapshots = pyrs.Snapshots(*shuffled)
        assert_that(tuple(snapshots)).is_equal_to(self.DATA)

    def test_filter(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        dailies = snapshots._filter('days')
        weeklies = snapshots._filter('weeks')
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
        first = pyrs.FREQUENCIES[0:-1]
        last = pyrs.FREQUENCIES[1:]
        for small, big in zip(first, last):
            assert_that(pyrs.next_frequency(small)).is_equal_to(big)
        assert_that(pyrs.next_frequency).raises(IndexError).when_called_with(big)

    def test_rotate(self):
        snapshots = pyrs.Snapshots(*self.DATA)
        assert_that(snapshots.should_rotate_up('hours')).is_true()
        assert_that(snapshots.should_rotate_up('days')).is_false()
        assert_that(snapshots.should_rotate_up('weeks')).is_true()
        assert_that(snapshots.should_rotate_up('months')).is_false()
        assert_that(snapshots.should_rotate_up('years')).is_true()
