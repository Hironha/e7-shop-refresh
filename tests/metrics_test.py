import datetime as dt

from src.metrics import MetricsOverview, MetricsProcessor, MetricsSummary, RefreshMetric


def test_summarize() -> None:
    now = dt.datetime.now(dt.UTC)
    metrics = [
        RefreshMetric(now, 10, 2, 1),
        RefreshMetric(now, 20, 4, 2),
        RefreshMetric(now, 50, 7, 0),
        RefreshMetric(now, 100, 8, 2),
    ]
    processor = MetricsProcessor()
    summary = processor.summarize(metrics)

    assert summary == MetricsSummary(
        iterations=180,
        covenants=21,
        covenant_bookmarks=105,
        covenant_gold=3_864_000,
        covenant_rating=21 / 180,
        mystics=5,
        msytic_medals=250,
        mystic_gold=1_400_000,
        mystic_rating=5 / 180,
        skystones=540,
        gold=5_264_000,
    )


def test_overview() -> None:
    now = dt.datetime.now(dt.UTC)
    metrics = [
        RefreshMetric(now, 10, 2, 1),
        RefreshMetric(now, 20, 4, 2),
    ]
    processor = MetricsProcessor()
    overview = processor.overview(metrics)
    assert len(overview) == 2

    first = overview[0]
    assert first == MetricsOverview(
        created_at=now,
        iterations=10,
        covenants=2,
        covenant_bookmarks=10,
        covenant_rating=2 / 10,
        covenant_gold=368_000,
        mystics=1,
        mystic_medals=50,
        mystic_gold=280_000,
        mystic_rating=1 / 10,
        skystones=30,
        gold=648_000,
    )

    second = overview[1]
    assert second == MetricsOverview(
        created_at=now,
        iterations=20,
        covenants=4,
        covenant_bookmarks=20,
        covenant_rating=4 / 20,
        covenant_gold=736_000,
        mystics=2,
        mystic_medals=100,
        mystic_gold=560_000,
        mystic_rating=2 / 20,
        skystones=60,
        gold=1_296_000,
    )
