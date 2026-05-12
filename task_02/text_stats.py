"""Модуль для подсчёта статистики текста.

Предоставляет функции для анализа текста:
количество слов, предложений, средняя длина слова,
топ-N самых частых слов.
"""

import re
from collections import Counter

# Минимальная длина слова. Однобуквенные токены (предлоги, союзы,
# частицы — в, к, о, с, у, а, и и др.) исключаются из подсчёта.
_MIN_WORD_LEN: int = 2


def _extract_words(text: str) -> list[str]:
    """Извлечь слова из текста, приводя к нижнему регистру.

    Однобуквенные токены (предлоги, союзы, частицы)
    исключаются из результата.

    Args:
        text: Исходный текст.

    Returns:
        Список слов длиной от _MIN_WORD_LEN символов.
    """
    words = re.findall(r"[^\W\d_]+", text.lower())
    return [w for w in words if len(w) >= _MIN_WORD_LEN]


def word_count(text: str) -> int:
    """Подсчитать количество слов в тексте.

    Однобуквенные токены исключаются из подсчёта.

    Args:
        text: Исходный текст.

    Returns:
        Число слов в тексте (длиной от 2 символов).
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

    # UTF-8 strict → кодировка консоли → fallback cp866.
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    raw = sys.stdin.buffer.read()
    console_enc = getattr(sys.stdin, "encoding", None) or "cp866"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode(console_enc)
        except (UnicodeDecodeError, LookupError):
            text = raw.decode("cp866", errors="replace")

    print(f"Слов: {word_count(text)}")
    print(f"Предложений: {sentence_count(text)}")
    print(f"Средняя длина слова: {avg_word_length(text):.1f}")
    print("Топ-5 слов:")
    for word, count in top_words(text):
        print(f"  {word}: {count}")
