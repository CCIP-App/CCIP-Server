import config
from mongoengine import connect

from models.attendee import Attendee, Scenario
from models.announcement import Announcement
from models.puzzle import PuzzleBucket, PuzzleStatus

connect(**config.MONGODB_SETTINGS)

__all__ = [
    'Announcement',
    'Attendee',
    'PuzzleBucket',
    'PuzzleStatus',
    'Scenario',
]
