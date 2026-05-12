# Правила агента
- Весь код на Python 3.11+ с type hints.
- Форматирование – black, линтер – ruff.
- Каждая функция содержит docstring.
- К каждой публичной функции пишется тест на pytest в файле tests/test_stats.py.
- Импорты сортированы: встроенные, затем сторонние, затем локальные.

# Структура проекта:
- app/main.py – точка входа
- app/models.py – модели
- app/db.py – работа с хранилищем
- app/routers/tasks.py – эндпоинты
- tests/test_api.py – тесты с TestClient