import csv
import datetime as dt
import os
from dataclasses import dataclass

from log import Logger
from result import Error, Ok, Result


@dataclass
class RefreshMetric:
    created_at: dt.datetime
    iterations: int
    covenant_count: int
    mystic_count: int


class MetricsStorage:
    def __init__(self, filepath: str, logger: Logger):
        self.__filepath = filepath
        self.__logger = logger
        self.__headers = ["created_at", "iterations", "covenant_count", "mystic_count"]

    def store(self, metric: RefreshMetric) -> Result[None, str]:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            with open(filepath, mode="w+", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(self.__headers)
                writer.writerow(self.__serialize_metric(metric))
                return Ok(None)

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return Error(f"Detected invalid headers in metrics file: {filepath}")

        with open(filepath, mode="a+", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.__serialize_metric(metric))
            self.__logger.info("Successfully Wrote content into CSV file")
            return Ok(None)

    def get_all_metrics(self) -> Result[list[RefreshMetric], str]:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            self.__logger.error(
                f"Failed getting all metrics from {filepath}. File empty or not found."
            )
            return Ok([])

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return Error("Missing or invalid headers from CSV file")

            metrics: list[RefreshMetric] = []
            for row in reader:
                match self.__deserialize_metric(row):
                    case Ok(metric):
                        metrics.append(metric)
                    case error:
                        return error

            return Ok(metrics)

    def tail(self, n: int) -> Result[list[RefreshMetric], str]:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            self.__logger.error(
                f"Failed getting last {n} metrics from {filepath}. File empty or not found."
            )
            return Ok([])

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return Error("Missing or invalid headers from CSV file")

            # reading a csv in reverse is actually kinda hard, so for now just load everything into memory
            lines = reversed(list(reader))
            metrics: list[RefreshMetric] = []
            for row in lines:
                if len(metrics) >= n:
                    break

                match self.__deserialize_metric(row):
                    case Ok(metric):
                        metrics.append(metric)
                    case error:
                        return error

            return Ok(metrics)

    def head(self, n: int) -> Result[list[RefreshMetric], str]:
        filepath = self.__filepath
        if not os.path.exists(filepath) or os.path.getsize(filepath) == 0:
            self.__logger.error(
                f"Failed getting first {n} metrics from {filepath}. File empty or not found."
            )
            return Ok([])

        with open(filepath, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers is None or headers != self.__headers:
                return Error("Missing or invalid headers from CSV file")

            metrics: list[RefreshMetric] = []
            for row in reader:
                if len(metrics) >= n:
                    break

                match self.__deserialize_metric(row):
                    case Ok(metric):
                        metrics.append(metric)
                    case error:
                        return error

            return Ok(metrics)

    def __serialize_metric(self, metric: RefreshMetric) -> list[str]:
        created_at = metric.created_at.isoformat(timespec="milliseconds")
        iterations = str(metric.iterations)
        covenant_count = str(metric.covenant_count)
        mystic_count = str(metric.mystic_count)
        # order matters and it must be the same order defined in headers
        return [created_at, iterations, covenant_count, mystic_count]

    def __deserialize_metric(self, row: list[str]) -> Result[RefreshMetric, str]:
        created_at = dt.datetime.fromisoformat(row[0])
        iterations = int(row[1])
        covenant_count = int(row[2])
        mystic_count = int(row[3])
        return Ok(RefreshMetric(created_at, iterations, covenant_count, mystic_count))


@dataclass(frozen=True)
class MetricsSummary:
    iterations: int
    covenants: int
    covenant_bookmarks: int
    covenant_gold: int
    covenant_rating: float
    mystics: int
    mystic_medals: int
    mystic_gold: int
    mystic_rating: float
    skystones: int
    gold: int


@dataclass(frozen=True)
class MetricsOverview:
    created_at: dt.datetime
    iterations: int
    covenants: int
    covenant_bookmarks: int
    covenant_rating: float
    covenant_gold: int
    mystics: int
    mystic_medals: int
    mystic_gold: int
    mystic_rating: float
    skystones: int
    gold: int


class MetricsProcessor:
    def __init__(self):
        self.__skystone_per_iteration = 3
        self.__medals_per_mystic = 50
        self.__booksmarks_per_covenant = 5
        self.__gold_per_covenant = 184_000
        self.__gold_per_mystic = 280_000

    def summarize(self, metrics: list[RefreshMetric]) -> MetricsSummary:
        iterations = 0
        covenants = 0
        mystics = 0
        for metric in metrics:
            iterations += metric.iterations
            covenants += metric.covenant_count
            mystics += metric.mystic_count

        skystones = self.__skystone_per_iteration * iterations
        covenant_medals = self.__booksmarks_per_covenant * covenants
        covenant_gold = self.__gold_per_covenant * covenants
        covenant_rating = covenants / iterations

        mystic_medals = self.__medals_per_mystic * mystics
        mystic_gold = self.__gold_per_mystic * mystics
        mystic_rating = mystics / iterations

        gold = covenant_gold + mystic_gold

        return MetricsSummary(
            iterations=iterations,
            covenants=covenants,
            covenant_bookmarks=covenant_medals,
            covenant_gold=covenant_gold,
            covenant_rating=covenant_rating,
            mystics=mystics,
            mystic_medals=mystic_medals,
            mystic_gold=mystic_gold,
            mystic_rating=mystic_rating,
            gold=gold,
            skystones=skystones,
        )

    def overview(self, metrics: list[RefreshMetric]) -> list[MetricsOverview]:
        overview: list[MetricsOverview] = []
        for metric in metrics:
            skystones = self.__skystone_per_iteration * metric.iterations
            covenant_bookmarks = self.__booksmarks_per_covenant * metric.covenant_count
            covenant_gold = self.__gold_per_covenant * metric.covenant_count
            covenant_rating = metric.covenant_count / metric.iterations

            mystic_medals = self.__medals_per_mystic * metric.mystic_count
            mystic_gold = self.__gold_per_mystic * metric.mystic_count
            mystic_rating = metric.mystic_count / metric.iterations

            gold = covenant_gold + mystic_gold
            overview.append(
                MetricsOverview(
                    created_at=metric.created_at,
                    iterations=metric.iterations,
                    covenants=metric.covenant_count,
                    covenant_bookmarks=covenant_bookmarks,
                    covenant_rating=covenant_rating,
                    covenant_gold=covenant_gold,
                    mystics=metric.mystic_count,
                    mystic_medals=mystic_medals,
                    mystic_gold=mystic_gold,
                    mystic_rating=mystic_rating,
                    skystones=skystones,
                    gold=gold,
                )
            )
        return overview
