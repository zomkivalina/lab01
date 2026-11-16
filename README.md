# Лабораторна робота №1. Основи функціонального програмування у Python

**Студентка:** Зьомків А. І., група ФЕП-21
**Варіант:** 6 — «Система доставки»

## Опис варіанта
**Вхідні дані:** посилки з вагою (кг), відстанню (км), типом доставки
(`economy` / `standard` / `express`) та статусом оплати (`paid`).

**Завдання:** відібрати оплачені посилки, що проходять критерій
прийнятності, розрахувати базову вартість доставки за тарифом, надбавки
та підсумкову суму, а також загальну виручку.

**Політики, що передаються через `typing.Callable`:**
- `TariffFn` — тариф: `(вага, відстань) -> базова вартість`;
- `SurchargeFn` — надбавка: `(посилка, база) -> надбавка`
  (за тип доставки та за важку посилку, комбінуються `combine_surcharges`);
- `AcceptFn` — критерій прийнятності: `(посилка) -> bool`
  (максимальна вага та відстань);
- `NowFn` — постачальник часу для позначки звіту (інжекція залежності).

## Структура проєкту
```
lab01/
├── README.md               # опис і команди запуску
├── core.py                 # чисте ядро (без I/O, глобалів і мутацій)
├── app.py                  # оболонка I/O: читання JSON, час, print
├── starter_imperative.py   # вихідний імперативний варіант (для порівняння)
├── data/parcels.json       # вхідні дані
├── tests/test_core.py      # pytest-тести
├── pytest.ini              # налаштування pytest (pythonpath)
└── requirements.txt        # pytest, mypy, black, ruff
```

**`core.py`:**
- базові чисті функції: `is_paid`, `base_cost`, `with_cost`, `price_parcel`, `summarize`;
- `process_parcels_pure` — завдання 1, усі параметри передаються явно;
- `make_processor` — функція вищого порядку (фабрика обробника), завдання 2;
- фабрики політик: `make_linear_tariff`, `make_type_surcharge`,
  `make_heavy_surcharge`, `combine_surcharges`, `make_acceptance`;
- `stamp_total` — завдання 3 (час передається як `Callable`);
- додаткові вправи: `compose`, `make_multiplier`, `express_ids`.

**`app.py`:** `load_parcels` (читання файлу), `render_report` (друк),
`main` (конфігурація політик і запуск).

## Запуск
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

python app.py                 # запуск програми
pytest -v                     # тести
mypy core.py app.py tests/    # перевірка типів
black --check .               # форматування
ruff check .                  # лінтер
```
