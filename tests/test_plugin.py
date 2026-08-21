import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1].parent))

from sakuramedia_judge_collecttion_movie.plugin import judge_movies
from sakuramedia_judge_collecttion_movie.settings import DurationCollectionSettings

from src.plugins.types import MoviePage, MovieSnapshot


class FakeMovieApi:
    def __init__(self, snapshots):
        self.snapshots = snapshots
        self.patches = []

    def list_page(self, *, after_id=0, limit=500):
        rows = [snapshot for snapshot in self.snapshots if snapshot.movie_id > after_id]
        rows = rows[:limit]
        return MoviePage(items=tuple(rows), next_cursor=None)

    def patch(self, movie_id, fields, expected_revision):
        self.patches.append((movie_id, fields, expected_revision))
        return True


class FakeContext:
    plugin_id = "sakuramedia_judge_collecttion_movie"

    def __init__(self, snapshots):
        self.movies = FakeMovieApi(snapshots)

    @staticmethod
    def get_task_logger(_name):
        return SimpleNamespace(info=lambda *args, **kwargs: None)


def _snapshot(movie_id, duration, is_collection, owners=None):
    return MovieSnapshot(
        movie_id=movie_id,
        revision=0,
        values={
            "duration_minutes": duration,
            "is_collection": is_collection,
        },
        owners=owners or {},
    )


def test_default_threshold_is_300_minutes():
    assert DurationCollectionSettings().duration_threshold_minutes == 300


def test_judge_movies_uses_duration_threshold_and_respects_owner():
    context = FakeContext(
        [
            _snapshot(1, 180, False),
            _snapshot(2, 60, True),
            _snapshot(3, 180, False, {"is_collection": "host:manual"}),
            _snapshot(4, 0, False),
        ]
    )

    stats = judge_movies(context, DurationCollectionSettings(duration_threshold_minutes=120))

    assert stats == {
        "scanned": 4,
        "updated": 2,
        "unchanged": 1,
        "skipped_owned": 1,
        "patch_failed": 0,
    }
    assert context.movies.patches == [
        (1, {"is_collection": True}, 0),
        (2, {"is_collection": False}, 0),
    ]
