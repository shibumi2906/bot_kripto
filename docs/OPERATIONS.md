# Запуск и обслуживание v0.3

Из корня репозитория, Python 3.13. Активация окружения необязательна.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m app analyze --mode demo
```

Если .venv уже работает, используйте его. Старые .venv1 и .venv_py312_broken_20260722 не используются. На Linux путь к интерпретатору — .venv/bin/python.

## Режимы

Demo: фиксированные искусственные свечи с mode=demo и фиксированным as_of; сеть не нужна. Live: публичные часовые свечи Binance, OKX и Kraken; все цены в USDT. Не меньше двух свежих согласованных по времени источников. Получить API-ключи этих бирж для этого режима не требуется.

```powershell
.\.venv\Scripts\python.exe -m app analyze --mode live --symbol BTCUSDT --balance 1000
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Swagger: /docs, демо: /analysis/demo. POST /analysis принимает symbol, mode, explain, balance, risk_percent. Для HTTP explain по умолчанию запрещён. Остановка — Ctrl+C.

Версия ядра technical-v2: risk.data_quality, risk.market и risk.position разделены. Live дополнительно загружает bid/ask. При отсутствии двух валидных свежих котировок отчёт остаётся доступен, но действие HOLD и trade_plan=null. Сценарий также блокируют недостаточная торговая активность, спред >0.2% и отклонение от анализируемого закрытия >0.5%.

## Ключи и модель

В новом checkout создайте .env из .env.example. Существующий файл не перезаписывайте. Переменные процесса имеют приоритет. Не присылайте ключи в чат.

| Настройка | Назначение |
| --- | --- |
| TELEGRAM_BOT_TOKEN | Telegram polling; для CLI и API не нужен |
| OPENAI_API_KEY | Только для явно запрошенного AI-комментария |
| OPENAI_MODEL | gpt-6.1-sol по умолчанию |
| OPENAI_DAILY_TOKEN_LIMIT | 200000, допускается уменьшение вплоть до нуля |
| OPENAI_MAX_OUTPUT_TOKENS | 2048, включая reasoning; допустимо 256..8192 |
| OPENAI_BUDGET_DB | .local/openai_budget.sqlite3 |
| OPENAI_HTTP_EXPLANATIONS_ENABLED | false; включать только за внешней авторизацией и лимитами |

```powershell
.\.venv\Scripts\python.exe -m app analyze --mode demo --explain
.\.venv\Scripts\python.exe -m app budget
.\.venv\Scripts\python.exe -m app doctor
```

--explain может расходовать платные токены. Бесплатность выбранной модели и участие проекта проверяются в кабинете OpenAI. Локальный счётчик не видит другие программы/проекты.

Счётчик атомарно резервирует верхнюю оценку текста в UTF-8 байтах + 4096 запаса + максимальный вывод. Поддерживаются только два текстовых сообщения без tools/media/history, до 32768 байт. Резерв не возвращается после ответа или ошибки. reported_usage хранит фактический usage API отдельно. Смена суток — 00:00 UTC.

Не удаляйте и не меняйте путь журнала в течение суток: это обнулит локальную защиту. Для нескольких процессов используйте один абсолютный путь на локальном диске; разные компьютеры не делят этот лимит. На границе суток лимит относится к дню отправки запроса, не является точным зеркалом провайдерского биллинга.

## Telegram

```powershell
.\.venv\Scripts\python.exe -m app.bot
```

/demo BTCUSDT — фиксированный пример; /analyze BTCUSDT — live. AI из Telegram не вызывается. Подписки, оплата и middleware старого прототипа отключены в демонстрационной сборке. Не запускайте два polling-процесса одновременно.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

Все тесты автономны; реальные ключи не нужны, AI и HTTP провайдеры подменяются. Тесты не меняют рабочую БД. В среде Codex на Windows выявлено ограничение socketpair: зависание asyncio внутри песочницы устранялось запуском тестов с разрешёнными локальными сокетами. Это не обходят изменением стратегии анализа.

Для проверки сети используйте live CLI без --explain. collection_errors и rejected_sources показывают недоступные/отбракованные источники. Недостаток свежих данных даёт CLI exit=2 или HTTP 503.

## Ограничения эксплуатации

Это локальное портфолио-приложение, не публичный SaaS. Нет аутентификации, пользовательских лимитов и scheduler в HTTP. Основное приложение не использует БД пользователей, Redis и Alembic. Журнал AI — отдельная SQLite БД. Резервную копию журнала делайте при остановленных процессах. Реальные секреты и журнал не должны попадать в Git.
