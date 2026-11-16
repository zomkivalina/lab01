from copy import deepcopy

import pytest

from core import (
    Parcel,
    combine_surcharges,
    compose,
    express_ids,
    make_acceptance,
    make_heavy_surcharge,
    make_linear_tariff,
    make_multiplier,
    make_processor,
    make_type_surcharge,
    process_parcels_pure,
    stamp_total,
    with_cost,
)

PURE_ARGS = {
    "price_per_kg": 5.0,
    "price_per_km": 0.5,
    "express_rate": 0.5,
    "max_weight": 30.0,
}


@pytest.fixture
def sample_parcels() -> list[Parcel]:
    return [
        {
            "id": 1,
            "weight": 2.0,
            "distance": 100.0,
            "delivery_type": "standard",
            "paid": True,
        },
        {
            "id": 2,
            "weight": 4.0,
            "distance": 50.0,
            "delivery_type": "express",
            "paid": True,
        },
        {
            "id": 3,
            "weight": 1.0,
            "distance": 10.0,
            "delivery_type": "economy",
            "paid": False,
        },
        {
            "id": 4,
            "weight": 40.0,
            "distance": 20.0,
            "delivery_type": "standard",
            "paid": True,
        },
    ]


def test_referential_transparency(sample_parcels: list[Parcel]) -> None:
    r1 = process_parcels_pure(sample_parcels, **PURE_ARGS)
    r2 = process_parcels_pure(sample_parcels, **PURE_ARGS)
    assert r1 == r2


def test_processor_referential_transparency(sample_parcels: list[Parcel]) -> None:
    process = make_processor(
        accept=lambda p: True,
        tariff=lambda w, d: w + d,
        surcharge=lambda p, b: 0.0,
    )
    assert process(sample_parcels) == process(sample_parcels)


def test_no_mutation(sample_parcels: list[Parcel]) -> None:
    original = deepcopy(sample_parcels)
    process_parcels_pure(sample_parcels, **PURE_ARGS)
    make_processor(
        accept=lambda p: True, tariff=lambda w, d: 1.0, surcharge=lambda p, b: 1.0
    )(sample_parcels)
    assert sample_parcels == original


def test_with_cost_returns_new_record() -> None:
    parcel: Parcel = {
        "id": 7,
        "weight": 1.0,
        "distance": 1.0,
        "delivery_type": "economy",
    }
    priced = with_cost(parcel, 10.0, 2.5)
    assert priced is not parcel
    assert priced["total"] == 12.5
    assert "total" not in parcel


def test_process_parcels_pure_values(sample_parcels: list[Parcel]) -> None:
    result = process_parcels_pure(sample_parcels, **PURE_ARGS)
    # №1: 2*5 + 100*0.5 = 60; №2: (4*5 + 50*0.5) = 45 + 50% = 67.5
    # №3 не оплачена, №4 важча за 30 кг
    assert result["count"] == 2
    assert [p["total"] for p in result["parcels"]] == [60.0, 67.5]
    assert result["revenue"] == pytest.approx(127.5)


def test_callable_policies(sample_parcels: list[Parcel]) -> None:
    tariff = make_linear_tariff(start_fee=40.0, per_kg=6.0, per_km=0.35, min_cost=60.0)
    surcharge = combine_surcharges(
        make_type_surcharge({"standard": 0.1, "express": 0.5}),
        make_heavy_surcharge(threshold=20.0, fee=150.0),
    )
    accept = make_acceptance(max_weight=30.0, max_distance=1000.0)
    result = make_processor(accept=accept, tariff=tariff, surcharge=surcharge)(
        sample_parcels
    )

    # №1: база 40+12+35 = 87, надбавка 8.7 -> 95.7
    # №2: база 40+24+17.5 = 81.5, надбавка 40.75 -> 122.25
    assert result["count"] == 2
    first, second = result["parcels"]
    assert (first["base_cost"], first["surcharge"], first["total"]) == (87.0, 8.7, 95.7)
    assert second["total"] == pytest.approx(122.25)
    assert result["revenue"] == pytest.approx(217.95)


def test_policies_are_replaceable(sample_parcels: list[Parcel]) -> None:
    flat = make_processor(
        accept=lambda p: True, tariff=lambda w, d: 100.0, surcharge=lambda p, b: 0.0
    )
    result = flat(sample_parcels)
    assert result["count"] == 3  # усі оплачені
    assert result["revenue"] == pytest.approx(300.0)


def test_min_cost_and_heavy_surcharge() -> None:
    tariff = make_linear_tariff(start_fee=0.0, per_kg=1.0, per_km=0.0, min_cost=60.0)
    assert tariff(2.0, 5.0) == 60.0
    heavy = make_heavy_surcharge(threshold=20.0, fee=150.0)
    assert heavy({"weight": 25.0}, 0.0) == 150.0
    assert heavy({"weight": 5.0}, 0.0) == 0.0


def test_type_surcharge_copies_rates() -> None:
    rates = {"express": 0.5}
    rule = make_type_surcharge(rates)
    rates["express"] = 10.0  # зміна ззовні не впливає на політику
    assert rule({"delivery_type": "express"}, 100.0) == 50.0


def test_stamp_total_uses_injected_time() -> None:
    assert stamp_total(99.9, lambda: 1700000000.0) == (99.9, 1700000000.0)


def test_compose_and_multiplier() -> None:
    double_then_inc = compose(lambda x: x + 1, make_multiplier(2))
    assert double_then_inc(5) == 11
    assert make_multiplier(3)(4) == 12


def test_express_ids(sample_parcels: list[Parcel]) -> None:
    assert express_ids(sample_parcels) == [2]
