"""Чисте ядро: розрахунок вартості доставки посилок (варіант 6).

Усі функції модуля детерміновані, не виконують I/O, не читають і не
змінюють глобальний стан та не мутують вхідні дані.
"""

from collections.abc import Callable, Iterable, Mapping
from typing import TypedDict, TypeVar


class Parcel(TypedDict, total=False):
    id: int
    weight: float  # кг
    distance: float  # км
    delivery_type: str  # "economy" | "standard" | "express"
    paid: bool
    base_cost: float  # з'являється в результаті
    surcharge: float  # з'являється в результаті
    total: float  # з'являється в результаті


class DeliveryReport(TypedDict):
    count: int
    revenue: float
    parcels: list[Parcel]


# Політики, що передаються ззовні
TariffFn = Callable[[float, float], float]  # (вага, відстань) -> базова ціна
SurchargeFn = Callable[[Parcel, float], float]  # (посилка, база) -> надбавка
AcceptFn = Callable[[Parcel], bool]  # (посилка) -> чи приймаємо
ProcessorFn = Callable[[Iterable[Parcel]], DeliveryReport]
NowFn = Callable[[], float]

A = TypeVar("A")
B = TypeVar("B")
C = TypeVar("C")


# ---------- Базові чисті функції предметної області ----------


def is_paid(parcel: Parcel) -> bool:
    return bool(parcel.get("paid", False))


def base_cost(parcel: Parcel, tariff: TariffFn) -> float:
    return tariff(parcel["weight"], parcel["distance"])


def with_cost(parcel: Parcel, base: float, surcharge: float) -> Parcel:
    """Повертає НОВИЙ запис посилки з розрахованими полями."""
    return {
        **parcel,
        "base_cost": round(base, 2),
        "surcharge": round(surcharge, 2),
        "total": round(base + surcharge, 2),
    }


def price_parcel(parcel: Parcel, tariff: TariffFn, surcharge: SurchargeFn) -> Parcel:
    base = base_cost(parcel, tariff)
    return with_cost(parcel, base, surcharge(parcel, base))


def summarize(parcels: list[Parcel]) -> DeliveryReport:
    return {
        "count": len(parcels),
        "revenue": round(sum(p["total"] for p in parcels), 2),
        "parcels": parcels,
    }


# ---------- Завдання 1: явні параметри замість глобалів ----------


def process_parcels_pure(
    parcels: Iterable[Parcel],
    *,
    price_per_kg: float,
    price_per_km: float,
    express_rate: float,
    max_weight: float,
) -> DeliveryReport:
    def tariff(weight: float, distance: float) -> float:
        return weight * price_per_kg + distance * price_per_km

    def surcharge(parcel: Parcel, base: float) -> float:
        return base * express_rate if parcel["delivery_type"] == "express" else 0.0

    priced = [
        price_parcel(p, tariff, surcharge)
        for p in parcels
        if is_paid(p) and p["weight"] <= max_weight
    ]
    return summarize(priced)


# ---------- Завдання 2: параметризація через Callable ----------


def make_processor(
    *,
    accept: AcceptFn,
    tariff: TariffFn,
    surcharge: SurchargeFn,
) -> ProcessorFn:
    """Фабрика: повертає обробник, налаштований переданими політиками."""

    def process(parcels: Iterable[Parcel]) -> DeliveryReport:
        priced = [
            price_parcel(p, tariff, surcharge)
            for p in parcels
            if is_paid(p) and accept(p)
        ]
        return summarize(priced)

    return process


# ---------- Фабрики політик ----------


def make_linear_tariff(
    *, start_fee: float, per_kg: float, per_km: float, min_cost: float
) -> TariffFn:
    def tariff(weight: float, distance: float) -> float:
        return max(min_cost, start_fee + weight * per_kg + distance * per_km)

    return tariff


def make_type_surcharge(rates: Mapping[str, float]) -> SurchargeFn:
    """Надбавка як частка від бази залежно від типу доставки."""
    frozen = dict(rates)  # власна копія: зміна rates ззовні не вплине

    def surcharge(parcel: Parcel, base: float) -> float:
        return base * frozen.get(parcel["delivery_type"], 0.0)

    return surcharge


def make_heavy_surcharge(*, threshold: float, fee: float) -> SurchargeFn:
    def surcharge(parcel: Parcel, base: float) -> float:
        return fee if parcel["weight"] > threshold else 0.0

    return surcharge


def combine_surcharges(*rules: SurchargeFn) -> SurchargeFn:
    """Сумарна надбавка з кількох незалежних правил."""

    def surcharge(parcel: Parcel, base: float) -> float:
        return sum(rule(parcel, base) for rule in rules)

    return surcharge


def make_acceptance(*, max_weight: float, max_distance: float) -> AcceptFn:
    def accept(parcel: Parcel) -> bool:
        return parcel["weight"] <= max_weight and parcel["distance"] <= max_distance

    return accept


# ---------- Завдання 3: інжекція залежності від часу ----------


def stamp_total(total: float, now: NowFn) -> tuple[float, float]:
    """Чиста щодо total: «час» приходить ззовні через Callable."""
    return total, now()


# ---------- Додаткові вправи ----------


def compose(f: Callable[[B], C], g: Callable[[A], B]) -> Callable[[A], C]:
    return lambda x: f(g(x))


def make_multiplier(k: int) -> Callable[[int], int]:
    return lambda x: x * k


def express_ids(parcels: Iterable[Parcel]) -> list[int]:
    """Замість append у циклі: новий список через list comprehension."""
    return [p["id"] for p in parcels if p["delivery_type"] == "express"]


def make_rate(k: float) -> Callable[[float], float]:
    return lambda x: x * k


def round_money(x: float) -> float:
    return round(x, 2)
