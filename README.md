# TimeManagerWindows

Коротко: современное «экранное время» для Windows. Приложение фиксирует активное окно и суммирует время по приложениям в SQLite (`usage.db`). GUI на PyQt5 с вкладками «Сегодня» и «Все время», поиском, сортировкой и автообновлением.

## Возможности
- Учёт активного приложения с агрегацией по дням
- Вкладки «Сегодня» и «Все время»
- Поиск, сортировка по столбцам, тёмная тема
- Автообновление каждые 2 секунды

## Установка и запуск
### Вариант 1: Poetry
```bash
poetry install
poetry run python main.py
```

### Вариант 2: pip
```bash
pip install PyQt5 psutil pywin32
python main.py
```

Требования: Windows 10+, Python 3.12+, права для pywin32 (доступ к активному окну/процессам).

## База данных
- Файл: `usage.db`
- Таблица: `usage(name_process, date, time, time_type)`
- Время автоматически нормализуется в секунды/минуты/часы

## Игнорируемые процессы
Чтобы не учитывать системные окна и служебные процессы, в `usage.py` есть константа `IGNORED_APPS`. Текущий список:

```
Explorer, Windowsterminal, Taskmgr, Unknown, Applicationframehost,
Runtimebroker, Startmenuexperiencehost, Searchexperiencehost, Searchui,
Shelleexperiencehost, Systemsettings, Textinputhost, Ctfmon, Dllhost,
Wwahost, Yourphone, Widgets
```

Вы можете расширить список, добавив названия в `IGNORED_APPS` (они приводятся к формату `.title()`).

## Структура
- `usage.py` — трекинг активного окна и работа с SQLite
- `main.py` — PyQt5 GUI (вкладки, таблицы, поиск, стиль, таймер)
- `pyproject.toml` — зависимости (PyQt5, psutil, pywin32)

## Идеи для расширения
- Экспорт CSV/Excel
- Графики за день/неделю (PyQtGraph)
- Иконка в трее и пауза трекинга
- Редактируемый список исключений в самом GUI 