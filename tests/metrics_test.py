import datetime as dt

from src.metrics import MetricsProcessor, MetricsSummary, RefreshMetric


def test_get_metrics_summary() -> None:
    now = dt.datetime.now(dt.UTC)
    metrics = [
        RefreshMetric(now, 10, 2, 1),
        RefreshMetric(now, 20, 4, 2),
        RefreshMetric(now, 50, 7, 0),
        RefreshMetric(now, 100, 8, 2),
    ]
    processor = MetricsProcessor()
    summary = processor.get_metrics_summary(metrics)

    assert summary == MetricsSummary(
        total_iterations=180,
        total_covenants=21,
        total_covenants_medals=105,
        total_covenants_gold=3_864_000,
        covenant_rating=21 / 180,
        total_mystics=5,
        total_mystics_medals=25,
        total_mystics_gold=1_400_000,
        mystic_rating=5 / 180,
        total_skystones=540,
        total_gold=5_264_000,
    )
