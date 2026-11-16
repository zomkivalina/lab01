"""Оболонка побічних ефектів: читання файлу, час, виведення звіту."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from core import (
    DeliveryReport,
    Parcel,
    combine_surcharges,
    compose,
    express_ids,
    make_acceptance,
    make_heavy_surcharge,
    make_linear_tariff,
    make_processor,
    make_rate,
    make_type_surcharge,
    round_money,
    stamp_total,
)

DATA_FILE = Path(__file__).parent / "data" / "parcels.json"

TYPE_NAMES = {"economy": "економ", "standard": "стандарт", "express": "експрес"}


def load_parcels(path: Path) -> list[Parcel]:
    with path.open(encoding="utf-8") as f:
        data: list[Parcel] = json.load(f)
    return data


def render_report(report: DeliveryReport, generated_at: float) -> None:
    stamp = (
        datetime.fromtimestamp(generated_at, tz=timezone.utc)
        .astimezone()
        .strftime("%d.%m.%Y %H:%M:%S")
    )
    print("=" * 66)
    print(f"  ЗВІТ СЛУЖБИ ДОСТАВКИ        сформовано: {stamp}")
    print("=" * 66)
    print(
        f"{'ID':>4} | {'Тип':<8} | {'Вага':>6} | {'Км':>5} | "
        f"{'База':>7} | {'Надб.':>7} | {'Разом':>8}"
    )
    print("-" * 66)
    for p in report["parcels"]:
        print(
            f"{p['id']:>4} | {TYPE_NAMES[p['delivery_type']]:<8} | "
            f"{p['weight']:>6.1f} | {p['distance']:>5.0f} | "
            f"{p['base_cost']:>7.2f} | {p['surcharge']:>7.2f} | {p['total']:>8.2f}"
        )
    print("-" * 66)
    print(f"Прийнято до доставки: {report['count']} посилок")
    print(f"Загальна виручка:     {report['revenue']:.2f} грн")


def run() -> None:
    parcels = load_parcels(DATA_FILE)

    # Політики (усі параметри задаються тут, а не глобально в ядрі)
    tariff = make_linear_tariff(start_fee=40.0, per_kg=6.0, per_km=0.35, min_cost=60.0)
    surcharge = combine_surcharges(
        make_type_surcharge({"economy": 0.0, "standard": 0.1, "express": 0.5}),
        make_heavy_surcharge(threshold=20.0, fee=150.0),
    )
    accept = make_acceptance(max_weight=30.0, max_distance=1000.0)

    process = make_processor(accept=accept, tariff=tariff, surcharge=surcharge)
    report = process(parcels)

    revenue, generated_at = stamp_total(report["revenue"], time.time)
    render_report(report, generated_at)

    print()
    print(f"Експрес-посилки у вхідних даних: {express_ids(parcels)}")
    with_vat = compose(round_money, make_rate(1.2))
    print(f"Виручка з ПДВ 20% (compose): {with_vat(revenue):.2f} грн")
    print(f"Вхідні записи не змінено: {'total' not in parcels[0]}")


if __name__ == "__main__":
    run()
