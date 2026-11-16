"""Стартовий імперативний фрагмент для варіанту 6 (ДО рефакторингу).

Проблеми: глобальні тарифи, print усередині обчислень,
мутація вхідних словників, змішування обчислень та I/O.
"""

PRICE_PER_KG = 6.0  # глобальний стан
PRICE_PER_KM = 0.35
EXPRESS_RATE = 0.5


def process_parcels(parcels, max_weight):
    valid = []
    revenue = 0.0
    for p in parcels:
        if not p["paid"]:
            continue
        print("Processing parcel:", p["id"])  # побічний ефект
        cost = p["weight"] * PRICE_PER_KG + p["distance"] * PRICE_PER_KM
        if p["weight"] > max_weight:
            continue
        if p["delivery_type"] == "express":
            cost = cost * (1 + EXPRESS_RATE)
        p["total"] = cost  # мутуємо вхідні дані
        valid.append(p)
        revenue += cost
    return {"count": len(valid), "revenue": revenue, "parcels": valid}
