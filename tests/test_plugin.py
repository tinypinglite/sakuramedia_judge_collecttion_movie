import json
import sys
from pathlib import Path
from string import Formatter
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1].parent))

from sakuramedia_judge_collecttion_movie.plugin import judge_movies, register
from sakuramedia_judge_collecttion_movie.settings import DurationCollectionSettings

from src.i18n import LanguageState, reset_language_state, set_language_state
from src.plugins.i18n import PluginI18n
from src.plugins.types import MoviePage, MovieSnapshot, TagSnapshot

PLUGIN_DIR = Path(__file__).resolve().parents[1]


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
    settings = {}

    def __init__(self, snapshots):
        self.movies = FakeMovieApi(snapshots)

    @property
    def i18n(self):
        return PluginI18n(self.plugin_id, PLUGIN_DIR)

    @staticmethod
    def get_task_logger(_name):
        return SimpleNamespace(info=lambda *args, **kwargs: None)


class FakeReporter:
    def __init__(self):
        self.progress = []

    def progress_callback(self, payload):
        self.progress.append(dict(payload))


def _snapshot(
    movie_id,
    duration,
    is_collection,
    owners=None,
    movie_number="ABP-001",
    tags=(),
):
    return MovieSnapshot(
        movie_id=movie_id,
        revision=0,
        values={
            "duration_minutes": duration,
            "movie_number": movie_number,
            "is_collection": is_collection,
        },
        owners=owners or {},
        tags=tuple(TagSnapshot(tag_id=index, name=name) for index, name in enumerate(tags, 1)),
    )


def test_default_threshold_is_300_minutes():
    settings = DurationCollectionSettings()

    assert settings.duration_threshold_minutes == 300
    assert settings.number_features == {"OFJE", "CJOB", "DVAJ", "REBD"}
    assert settings.suffix_number_features == set()
    assert settings.tag_names == set()


def test_judge_movies_marks_only_collections_and_respects_owner():
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
        "updated": 1,
        "unchanged": 2,
        "skipped_owned": 1,
        "patch_failed": 0,
    }
    assert context.movies.patches == [
        (1, {"is_collection": True}, 0),
    ]


def test_judge_movies_marks_number_feature_below_duration_threshold():
    context = FakeContext(
        [
            _snapshot(1, 240, False, movie_number="OFJE-546"),
            _snapshot(2, 240, False, movie_number="ABP-001"),
        ]
    )

    stats = judge_movies(
        context,
        DurationCollectionSettings(
            duration_threshold_minutes=300,
            number_features={" ofje "},
        ),
    )

    assert stats == {
        "scanned": 2,
        "updated": 1,
        "unchanged": 1,
        "skipped_owned": 0,
        "patch_failed": 0,
    }
    assert context.movies.patches == [(1, {"is_collection": True}, 0)]


def test_judge_movies_marks_suffix_number_feature_below_duration_threshold():
    context = FakeContext(
        [
            _snapshot(1, 240, False, movie_number="STAR-600-V"),
            _snapshot(2, 240, False, movie_number="STAR-600"),
        ]
    )

    stats = judge_movies(
        context,
        DurationCollectionSettings(
            duration_threshold_minutes=300,
            suffix_number_features={" -v "},
        ),
    )

    assert stats == {
        "scanned": 2,
        "updated": 1,
        "unchanged": 1,
        "skipped_owned": 0,
        "patch_failed": 0,
    }
    assert context.movies.patches == [(1, {"is_collection": True}, 0)]


def test_numeric_number_suffix_preserves_separator():
    for suffix, expected_id in (("_001", 1), ("-001", 2)):
        context = FakeContext([
            _snapshot(1, 60, False, movie_number="072625_001"),
            _snapshot(2, 60, False, movie_number="072625-001"),
        ])
        judge_movies(context, DurationCollectionSettings(suffix_number_features={suffix}))
        assert context.movies.patches == [(expected_id, {"is_collection": True}, 0)]


def test_judge_movies_marks_tag_match_below_duration_threshold():
    context = FakeContext([
        _snapshot(1, 60, False, tags=("4時間以上作品",)),
        _snapshot(2, 60, False, tags=("単体作品",)),
    ])

    stats = judge_movies(
        context,
        DurationCollectionSettings(
            duration_threshold_minutes=300,
            number_features=set(),
            tag_names={" 4時間以上作品 "},
        ),
    )

    assert stats == {
        "scanned": 2,
        "updated": 1,
        "unchanged": 1,
        "skipped_owned": 0,
        "patch_failed": 0,
    }
    assert context.movies.patches == [(1, {"is_collection": True}, 0)]


def test_judge_movies_tag_match_is_or_and_case_insensitive():
    context = FakeContext([
        _snapshot(1, 60, False, tags=("VR",)),
        _snapshot(2, 60, False, tags=("ハーレム", "巨乳")),
        _snapshot(3, 60, False, tags=("巨乳",)),
    ])

    stats = judge_movies(
        context,
        DurationCollectionSettings(
            number_features=set(),
            tag_names={"vr", "ハーレム"},
        ),
    )

    assert stats == {
        "scanned": 3,
        "updated": 2,
        "unchanged": 1,
        "skipped_owned": 0,
        "patch_failed": 0,
    }
    assert context.movies.patches == [
        (1, {"is_collection": True}, 0),
        (2, {"is_collection": True}, 0),
    ]


def _read_catalog(locale):
    path = PLUGIN_DIR / "i18n" / f"{locale}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _placeholders(template):
    return {name for _, name, _, _ in Formatter().parse(template) if name}


def test_catalogs_share_keys_and_placeholders():
    zh = _read_catalog("zh-CN")
    en = _read_catalog("en")

    assert zh.keys() == en.keys()
    for key, chinese in zh.items():
        assert chinese
        assert en[key]
        assert _placeholders(chinese) == _placeholders(en[key])


def test_manifest_declares_i18n_display_name():
    manifest = json.loads(
        (PLUGIN_DIR / "manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["host_api_version"] == 12
    assert manifest["display_name_i18n"] == {
        "zh-CN": manifest["display_name"],
        "en": "Detect collection movies by duration, number pattern or tag",
    }


def test_registration_localizes_display_name_and_cli_help():
    registration = register(FakeContext([]))
    display_name_i18n = registration.display_name_i18n
    job = registration.jobs[0]

    assert display_name_i18n["zh-CN"] == registration.display_name
    assert display_name_i18n["en"] != display_name_i18n["zh-CN"]
    assert display_name_i18n["en"] == (
        "Detect collection movies by duration, number pattern or tag"
    )
    assert job.cli_help_i18n["zh-CN"] == job.cli_help
    assert job.cli_help_i18n["en"] == (
        "Detect collection movies by duration, number pattern or tag"
    )


def test_settings_schema_exposes_i18n_titles():
    properties = DurationCollectionSettings.model_json_schema()["properties"]
    expected = {
        "duration_threshold_minutes": (
            "合集时长阈值（分钟）",
            "Collection duration threshold (minutes)",
        ),
        "number_features": ("番号前缀", "Movie number prefixes"),
        "suffix_number_features": ("番号后缀", "Movie number suffixes"),
        "tag_names": ("标签", "Tags"),
    }

    for field, (chinese, english) in expected.items():
        assert properties[field]["title"] == chinese
        assert properties[field]["title_i18n"] == {
            "zh-CN": chinese,
            "en": english,
        }


def _progress_text(language):
    context = FakeContext([_snapshot(1, 400, False), _snapshot(2, 60, True)])
    reporter = FakeReporter()
    token = set_language_state(LanguageState(user_language=language))
    try:
        judge_movies(context, DurationCollectionSettings(), reporter)
    finally:
        reset_language_state(token)
    return reporter.progress[-1]["text"]


def test_progress_text_follows_request_language():
    chinese = _progress_text("zh-CN")
    english = _progress_text("en")

    assert chinese == "扫描 2 部，已更新 1 部，跳过 owner 0 部"
    assert english == "Scanned 2 movies, updated 1, skipped 0 owned by others"
    assert chinese != english

