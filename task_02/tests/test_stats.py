"""Тесты для модуля text_stats."""

from text_stats import avg_word_length, sentence_count, top_words, word_count

# --- word_count ---


def test_word_count_simple() -> None:
    """Подсчёт слов в простом предложении."""
    assert word_count("Hello world") == 2


def test_word_count_empty() -> None:
    """Пустая строка даёт 0 слов."""
    assert word_count("") == 0


def test_word_count_with_punctuation() -> None:
    """Знаки препинания не считаются словами."""
    assert word_count("Hello, world! How are you?") == 5


def test_word_count_russian() -> None:
    """Подсчёт русских слов."""
    assert word_count("Привет мир") == 2


def test_word_count_mixed() -> None:
    """Смешанный русско-английский текст."""
    assert word_count("Hello мир test тест") == 4


# --- sentence_count ---


def test_sentence_count_simple() -> None:
    """Подсчёт предложений с точками."""
    assert sentence_count("One. Two. Three.") == 3


def test_sentence_count_exclamation() -> None:
    """Восклицательные знаки разделяют предложения."""
    assert sentence_count("Hello! World!") == 2


def test_sentence_count_question() -> None:
    """Вопросительные знаки разделяют предложения."""
    assert sentence_count("How? Why?") == 2


def test_sentence_count_mixed_endings() -> None:
    """Смешанные знаки конца предложения."""
    assert sentence_count("Hello! How are you? Fine.") == 3


def test_sentence_count_empty() -> None:
    """Пустая строка даёт 0 предложений."""
    assert sentence_count("") == 0


def test_sentence_count_no_ending() -> None:
    """Текст без точки в конце — 1 предложение."""
    assert sentence_count("No ending here") == 1


def test_sentence_count_multiple_dots() -> None:
    """Многоточие считается как один разделитель."""
    assert sentence_count("Wait... Then go.") == 2


# --- avg_word_length ---


def test_avg_word_length_simple() -> None:
    """Средняя длина слова в простом тексте."""
    # hi=2, world=5 → (2+5)/2 = 3.5
    assert avg_word_length("hi world") == 3.5


def test_avg_word_length_empty() -> None:
    """Пустая строка даёт 0.0."""
    assert avg_word_length("") == 0.0


def test_avg_word_length_single() -> None:
    """Одно слово — его длина."""
    assert avg_word_length("Hello") == 5.0


def test_avg_word_length_russian() -> None:
    """Средняя длина русских слов."""
    # привет=6, мир=3 → (6+3)/2 = 4.5
    assert avg_word_length("привет мир") == 4.5


# --- top_words ---


def test_top_words_default_n() -> None:
    """Топ-5 по умолчанию."""
    text = "a a a b b c"
    result = top_words(text)
    assert len(result) <= 5
    assert result[0] == ("a", 3)


def test_top_words_custom_n() -> None:
    """Топ-2 с явным n."""
    text = "x x y z"
    result = top_words(text, n=2)
    assert result == [("x", 2), ("y", 1)]


def test_top_words_empty() -> None:
    """Пустой текст даёт пустой список."""
    assert top_words("") == []


def test_top_words_case_insensitive() -> None:
    """Слова приводятся к нижнему регистру."""
    text = "Hello hello HELLO"
    assert top_words(text) == [("hello", 3)]


def test_top_words_fewer_than_n() -> None:
    """Уникальных слов меньше, чем n."""
    text = "one two"
    result = top_words(text, n=5)
    assert len(result) == 2


def test_top_words_russian() -> None:
    """Топ русских слов."""
    text = "кот кот собака"
    result = top_words(text, n=2)
    assert result[0] == ("кот", 2)
