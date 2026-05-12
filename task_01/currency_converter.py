#!/usr/bin/env python3
"""Конвертер валют через аргументы командной строки.

Источники курсов:
  - Онлайн: официальный сайт ЦБ РФ (https://www.cbr.ru/currency_base/daily/)
  - Оффлайн: фиксированные курсы (fallback)

Все курсы ЦБ РФ указаны относительно RUB. Конвертация между
любыми двумя валютами выполняется через кросс-курс через рубль.

Примеры использования:
    python currency_converter.py 100 USD RUB
    python currency_converter.py 50 EUR USD
    python currency_converter.py 1000 RUB EUR
    python currency_converter.py 100 USD RUB --offline
"""

import argparse
import re
import sys
import urllib.request
import urllib.error
from decimal import Decimal, ROUND_HALF_UP
from html.parser import HTMLParser


# URL страницы с ежедневными курсами ЦБ РФ
CBR_DAILY_URL = "https://www.cbr.ru/currency_base/daily/"

# Фиксированные курсы относительно RUB (fallback при недоступности сайта ЦБ)
# Формат: буквенный код -> (номинал, курс за номинал в RUB)
FALLBACK_RATES: dict[str, tuple[int, float]] = {
    "AUD": (1, 53.6791),
    "AZN": (1, 43.7037),
    "BYN": (1, 26.4654),
    "BGN": (1, 45.2890),
    "BRL": (1, 15.1110),
    "HUF": (100, 24.6104),
    "HKD": (10, 94.8867),
    "DKK": (1, 11.7022),
    "AED": (1, 20.2304),
    "USD": (1, 74.2963),
    "EUR": (1, 88.5490),
    "EGP": (10, 14.0988),
    "INR": (100, 78.6733),
    "KZT": (100, 16.0325),
    "CNY": (1, 10.0000),
    "KGS": (100, 84.9873),
    "CAD": (1, 54.4894),
    "MDL": (10, 43.3124),
    "NOK": (10, 80.4665),
    "PLN": (1, 20.6683),
    "RON": (1, 16.6984),
    "XDR": (1, 102.2235),
    "SGD": (1, 58.5517),
    "TJS": (10, 79.3162),
    "TRY": (10, 16.4382),
    "TMT": (1, 21.2275),
    "UZS": (10000, 61.1898),
    "UAH": (10, 16.9414),
    "GBP": (1, 101.2733),
    "CZK": (10, 35.9823),
    "SEK": (10, 80.7822),
    "CHF": (1, 95.4597),
    "KRW": (1000, 51.2106),
    "JPY": (100, 47.3255),
}


class CBRTableParser(HTMLParser):
    """Парсер HTML-таблицы курсов валют с сайта ЦБ РФ."""

    def __init__(self) -> None:
        super().__init__()
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._current_row: list[str] = []
        self._current_data = ""
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            for attr_name, attr_value in attrs:
                if attr_name == "class" and attr_value and "data" in attr_value:
                    self._in_table = True
        elif self._in_table and tag == "tr":
            self._in_row = True
            self._current_row = []
        elif self._in_row and tag == "td":
            self._in_cell = True
            self._current_data = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._in_table:
            self._in_table = False
        elif tag == "tr" and self._in_row:
            self._in_row = False
            if self._current_row:
                self.rows.append(self._current_row)
        elif tag == "td" and self._in_cell:
            self._in_cell = False
            self._current_row.append(self._current_data.strip())

    def handle_data(self, data: str) -> None:
        if self._in_cell:
            self._current_data += data


def fetch_cbr_rates() -> dict[str, tuple[int, Decimal]]:
    """Получает курсы валют с сайта ЦБ РФ.

    Returns:
        Словарь {буквенный_код: (номинал, курс_за_номинал_в_RUB)}.
        RUB всегда присутствует с номиналом 1 и курсом 1.

    Raises:
        RuntimeError: Если сайт недоступен или данные не распознаны.
    """
    try:
        req = urllib.request.Request(
            CBR_DAILY_URL,
            headers={"User-Agent": "CurrencyConverter/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Сайт ЦБ РФ недоступен: {exc}") from exc

    parser = CBRTableParser()
    parser.feed(html)

    rates: dict[str, tuple[int, Decimal]] = {"RUB": (1, Decimal("1"))}

    for row in parser.rows:
        # Ожидаемый формат: Цифр.код | Букв.код | Единиц | Валюта | Курс
        if len(row) != 5:
            continue

        letter_code = row[1].strip().upper()
        if not re.match(r"^[A-Z]{3}$", letter_code):
            continue

        try:
            nominal = int(row[2].strip())
            # Заменяем запятую на точку для Decimal
            rate_str = row[4].strip().replace(",", ".")
            rate = Decimal(rate_str)
        except (ValueError, IndexError):
            continue

        if nominal > 0 and rate > 0:
            rates[letter_code] = (nominal, rate)

    if len(rates) <= 1:
        raise RuntimeError("Не удалось распознать курсы на странице ЦБ РФ")

    return rates


def get_fallback_rates() -> dict[str, tuple[int, Decimal]]:
    """Возвращает фиксированные курсы (fallback).

    Returns:
        Словарь {буквенный_код: (номинал, курс_за_номинал_в_RUB)}.
    """
    rates: dict[str, tuple[int, Decimal]] = {"RUB": (1, Decimal("1"))}
    for code, (nominal, rate) in FALLBACK_RATES.items():
        rates[code] = (nominal, Decimal(str(rate)))
    return rates


def rate_to_rub(currency: str, rates: dict[str, tuple[int, Decimal]]) -> Decimal:
    """Вычисляет курс 1 единицы валюты в RUB.

    Args:
        currency: Буквенный код валюты.
        rates: Словарь курсов от ЦБ РФ.

    Returns:
        Стоимость 1 единицы валюты в рублях.

    Raises:
        ValueError: Если валюта не найдена.
    """
    if currency == "RUB":
        return Decimal("1")

    if currency not in rates:
        raise ValueError(
            f"Валюта {currency} не найдена. Доступные: {', '.join(sorted(rates))}"
        )

    nominal, rate = rates[currency]
    # курс за 1 единицу = rate / nominal
    return rate / Decimal(str(nominal))


def convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    offline: bool = False,
) -> Decimal:
    """Конвертирует сумму из одной валюты в другую.

    Курсы берутся с сайта ЦБ РФ (все относительно RUB).
    Конвертация между любыми валютами выполняется через кросс-курс:
      result = amount × (rate_from / rate_to)

    Args:
        amount: Сумма для конвертации.
        from_currency: Исходная валюта.
        to_currency: Целевая валюта.
        offline: Использовать только фиксированные курсы.

    Returns:
        Результат конвертации (Decimal, округлённый до 2 знаков).

    Raises:
        ValueError: Если валюта не поддерживается.
    """
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()

    if from_currency == to_currency:
        return Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    rates: dict[str, tuple[int, Decimal]]
    if offline:
        rates = get_fallback_rates()
    else:
        try:
            rates = fetch_cbr_rates()
        except RuntimeError as exc:
            print(
                f"⚠ Сайт ЦБ РФ недоступен ({exc}), используются фиксированные курсы",
                file=sys.stderr,
            )
            rates = get_fallback_rates()

    # Стоимость 1 единицы каждой валюты в RUB
    from_in_rub = rate_to_rub(from_currency, rates)
    to_in_rub = rate_to_rub(to_currency, rates)

    # Кросс-курс: from -> RUB -> to
    result = Decimal(str(amount)) * from_in_rub / to_in_rub
    return result.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Конвертер валют (источник: ЦБ РФ)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Примеры:
  python currency_converter.py 100 USD RUB
  python currency_converter.py 50 EUR USD
  python currency_converter.py 1000 RUB EUR
  python currency_converter.py 100 USD RUB --offline

Курсы берутся с сайта ЦБ РФ: https://www.cbr.ru/currency_base/daily/
Все валюты котируются относительно RUB. Конвертация между
любыми валютами выполняется через кросс-курс через рубль.""",
    )
    parser.add_argument("amount", type=float, help="Сумма для конвертации")
    parser.add_argument(
        "from_currency", type=str, help="Исходная валюта (ISO 4217, например USD)"
    )
    parser.add_argument(
        "to_currency", type=str, help="Целевая валюта (ISO 4217, например RUB)"
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Использовать только фиксированные курсы (без запроса к сайту ЦБ РФ)",
    )

    args = parser.parse_args()

    if args.amount < 0:
        parser.error("Сумма не может быть отрицательной")

    try:
        result = convert(
            amount=args.amount,
            from_currency=args.from_currency,
            to_currency=args.to_currency,
            offline=args.offline,
        )
        print(
            f"{args.amount} {args.from_currency.upper()} = {result} {args.to_currency.upper()}"
        )
    except ValueError as exc:
        print(f"❌ Ошибка: {exc}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"❌ Непредвиденная ошибка: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
