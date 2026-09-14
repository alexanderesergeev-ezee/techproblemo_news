# Источники: допуск, справочник, документация

## 1. Что проверено по устройству платформ
Telegram Bot API доставляет боту сообщения из каналов, в которых бот является участником. Это не универсальный интерфейс чтения любых чужих каналов. Метод `messages.getHistory` основного Telegram API предназначен для пользователей, не ботов. Программный доступ с пользовательской авторизацией — отдельная интеграция и не отменяет условий использования.

На 14.09.2026 Telegram Content Licensing содержит широкие ограничения на сбор и использование данных в связи с ИИ, включая не только обучение, но и deployment; описаны исключения с явно выраженным информированным согласием соответствующих пользователей в конкретном контексте. Нельзя считать произвольный публичный канал автоматически разрешённым корпусом для LLM. Это существенный договорный вопрос, не вывод о полном запрете любых ботов.

Требуется подтвердить допустимость конкретного способа получения и обработки. Права администратора на добавление бота не всегда означают права на весь опубликованный контент. RSS-обёртка над Telegram сама по себе не устраняет ограничений. Обычный RSS другого сайта также не означает автоматически неограниченную лицензию на тексты.

До проверки реальные Telegram-коннекторы отключены. Работу над приложением можно продолжать на синтетике либо на независимо допущенных источниках.

## 2. Справочник — пока шаблон, не готовый список
В этом пакете **нет выдуманных или якобы проверенных каналов**. Следующая исследовательская задача — отобрать 15–20 кандидатов, из которых 5–10 пригодны для пилота.

| Поле | Что фиксировать |
|---|---|
| id / name / locator | Стабильный ID, точное название и проверенный адрес |
| type | RSS, API, Telegram Bot updates либо отдельно согласованный вариант |
| topic / language | Тематика и язык |
| evidence | Какие свежие материалы подтверждают релевантность; без копирования запрещённого корпуса |
| source_quality | Первичный отчёт, профильное издание, агрегатор; это оценка, не гарантия истины |
| access_checked_at | Дата технической проверки и её результат |
| approval_state | candidate / approved / blocked |
| permission_ref | Ссылка/ID решения о получении, хранении, AI-обработке и доставке выдержек |
| llm_transfer_allowed | Разрешена ли передача выбранному внешнему провайдеру |
| retention_days | Срок хранения по допустимым условиям |
| enabled | Только после проверки доступа и прав |

Не публиковать в репозитории персональные переписки о разрешениях: достаточно защищённой ссылки/ID решения. Реестр не расширяется автоматически агентом в рабочем сервисе.

## 3. Задание на исследование каталога
Подбирать прежде всего реальные происшествия: официальные incident/status/postmortem источники; профильные каналы об отказах и надёжности; сообщения об изменениях, испортивших работу; происшествия с данными, инфраструктурой и зависимостями. Не подменять каталог технологическими новостями вообще. Отдельно показать релевантность и возможность использования: это разные критерии.

## 4. Проверенные первичные ссылки
Ссылки проверялись 14 сентября 2026 года. Не являются юридическим заключением и не подтверждают условия будущих источников.

- Telegram Bots FAQ: https://core.telegram.org/bots/faq
- Telegram Bot API: https://core.telegram.org/bots/api
- Telegram bot introduction: https://core.telegram.org/bots
- Telegram user history method: https://core.telegram.org/method/messages.getHistory
- Telegram Content Licensing: https://telegram.org/tos/content-licensing
- Telegram API Terms: https://core.telegram.org/api/terms
- Codex Cloud: https://developers.openai.com/codex/cloud/
- Codex AGENTS.md: https://developers.openai.com/codex/guides/agents-md/
- Codex environments: https://developers.openai.com/codex/cloud/environments/
- SQLite appropriate uses: https://sqlite.org/whentouse.html
- SQLite Backup API: https://sqlite.org/backup.html
- OpenRouter structured outputs: https://openrouter.ai/docs/guides/features/structured-outputs
- OpenRouter provider logging: https://openrouter.ai/docs/guides/privacy/provider-logging
- GigaCode coding assistant: https://gigacode.ru/docs/quick-start/
- GigaChat API: https://developers.sber.ru/portal/products/gigachat-api
- GitHub creation of repositories: https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository
- GitHub Mermaid diagrams: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams

GigaCode — coding-ассистент. Для обработки текстов рассматривается GigaChat API или другой LLM API, а не запуск coding-инструмента на каждом сообщении. Конкретную модель и её тариф в этом пакете не выбирали. OpenRouter поддерживает JSON Schema для совместимых моделей/эндпоинтов, но локальная валидация приложения всё равно обязательна.
