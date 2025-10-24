"""Wczytywanie danych z prawdziwych obserwacji order book."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List


REQUIRED_COLUMNS = (
    "timestamp",
    "symbol",
    "bid_price_1",
    "bid_size_1",
    "ask_price_1",
    "ask_size_1",
    "bid_price_2",
    "bid_size_2",
    "ask_price_2",
    "ask_size_2",
    "trade_volume",
)


@dataclass(slots=True)
class OrderBookSample:
    """Pojedyncza obserwacja poziomów 1-2 wraz z wolumenem transakcji."""

    timestamp: datetime
    bid_price_1: float
    bid_size_1: float
    ask_price_1: float
    ask_size_1: float
    bid_price_2: float
    bid_size_2: float
    ask_price_2: float
    ask_size_2: float
    trade_volume: float


@dataclass(slots=True)
class OrderBookSeries:
    """Sekwencja obserwacji dla danej pary."""

    symbol: str
    samples: List[OrderBookSample]


def _parse_timestamp(value: str) -> datetime:
    ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def load_order_book_csv(path: str | Path) -> Dict[str, OrderBookSeries]:
    """Zwraca serię order book opartą na rzeczywistych danych z Binance."""

    table: Dict[str, List[str]] = {column: [] for column in REQUIRED_COLUMNS}
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Brak nagłówków w pliku CSV")
        missing = [col for col in REQUIRED_COLUMNS if col not in reader.fieldnames]
        if missing:
            raise ValueError(f"Brak wymaganych kolumn: {missing}")
        for row in reader:
            for column in REQUIRED_COLUMNS:
                table[column].append(row[column])

    timestamps = [_parse_timestamp(value) for value in table["timestamp"]]
    order = sorted(range(len(timestamps)), key=timestamps.__getitem__)

    grouped: Dict[str, List[OrderBookSample]] = {}
    for idx in order:
        symbol = table["symbol"][idx]
        grouped.setdefault(symbol, []).append(
            OrderBookSample(
                timestamp=timestamps[idx],
                bid_price_1=float(table["bid_price_1"][idx]),
                bid_size_1=float(table["bid_size_1"][idx]),
                ask_price_1=float(table["ask_price_1"][idx]),
                ask_size_1=float(table["ask_size_1"][idx]),
                bid_price_2=float(table["bid_price_2"][idx]),
                bid_size_2=float(table["bid_size_2"][idx]),
                ask_price_2=float(table["ask_price_2"][idx]),
                ask_size_2=float(table["ask_size_2"][idx]),
                trade_volume=float(table["trade_volume"][idx]),
            )
        )

    return {symbol: OrderBookSeries(symbol=symbol, samples=samples) for symbol, samples in grouped.items()}


def slice_series(series: OrderBookSeries, step: int) -> Iterable[List[OrderBookSample]]:
    """Zwraca fragmenty serii o zadanej długości bez nakładania się."""

    if step <= 0:
        raise ValueError("step musi być dodatni")
    chunk: List[OrderBookSample] = []
    for sample in series.samples:
        chunk.append(sample)
        if len(chunk) == step:
            yield chunk
            chunk = []
    if chunk:
        yield chunk
