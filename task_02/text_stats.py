"""Модуль для подсчёта статистики текста.

Предоставляет функции для анализа текста:
количество слов, предложений, средняя длина слова,
топ-N самых частых слов.
"""

import re
from collections import Counter


def _extract_words(text: str) -> list[str]:
    """Извлечь слова из текста, приводя к нижнему регистру.

    Args:
        text: Исходный текст.

    Returns:
        Список слов в нижнем регистре.
    """
    return re.findall(r"[^\W\d_]+", text.lower())


def word_count(text: str) -> int:
    """Подсчитать количество слов в тексте.

    Args:
        text: Исходный текст.

    Returns:
        Число слов в тексте.
    """
    return len(_extract_words(text))


def sentence_count(text: str) -> int:
    """Подсчитать количество предложений в тексте.

    Предложением считается фрагмент, завершающийся
    точкой, восклицательным или вопросительным знаком.

    Args:
        text: Исходный текст.

    Returns:
        Число предложений. Минимум 1, если текст непустой.
    """
    if not text.strip():
        return 0
    sentences = re.split(r"[.!?]+", text)
    # Фильтруем пустые хвосты после разделения
    non_empty = [s for s in sentences if s.strip()]
    return max(len(non_empty), 1)


def avg_word_length(text: str) -> float:
    """Вычислить среднюю длину слова в тексте.

    Args:
        text: Исходный текст.

    Returns:
        Средняя длина слова. 0.0, если слов нет.
    """
    words = _extract_words(text)
    if not words:
        return 0.0
    return sum(len(w) for w in words) / len(words)


def top_words(text: str, n: int = 5) -> list[tuple[str, int]]:
    """Вернуть топ-N самых частых слов в тексте.

    Args:
        text: Исходный текст.
        n: Количество возвращаемых слов. По умолчанию 5.

    Returns:
        Список кортежей (слово, частота), отсортированный
        по убыванию частоты.
    """
    words = _extract_words(text)
    counter = Counter(words)
    return counter.most_common(n)


if __name__ == "__main__":
    import sys

    # Читаем stdin как сырые байты и пробуем декодировать.
    # На Windows команда type может транскодировать файл
    # в кодировку консоли (cp866/cp1251), поэтому пробуем
    # несколько кодировок: UTF-8 → cp1251 → cp866 → latin-1.
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    raw = sys.stdin.buffer.read()
    for enc in ("utf-8", "cp1251", "cp866", "latin-1"):
        try:
            text = raw.decode(enc)
            # Если кириллица распознана — кодировка верная
            if any("\u0400" <= ch <= "\u04FF" for ch in text[:200]):
                break
        except UnicodeDecodeError:
            continue
    else:
        text = raw.decode("utf-8", errors="replace")
    print(f"Слов: {word_count(text)}")
    print(f"Предложений: {sentence_count(text)}")
    print(f"Средняя длина слова: {avg_word_length(text):.1f}")
    print("Топ-5 слов:")
    for word, count in top_words(text):
        print(f"  {word}: {count}")
