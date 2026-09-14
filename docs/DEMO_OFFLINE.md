# Демонстрация offline-запуска

Запуск выполнен 14.09.2026 на синтетических данных, без сети, API и секретов. Использовалась
временная база, затем команда была повторена с теми же путями.

```console
$ PYTHONPATH=src python -m techproblemo_news run-once --offline --database /tmp/techproblemo-demo.sqlite3 --output /tmp/techproblemo-deliveries.jsonl
{"classified": 4, "duplicates": 0, "failed": 0, "needs_review": 1, "new": 12, "queued": 6, "read": 12, "sent": 6, "skipped_no_text": 1}
$ PYTHONPATH=src python -m techproblemo_news run-once --offline --database /tmp/techproblemo-demo.sqlite3 --output /tmp/techproblemo-deliveries.jsonl
{"classified": 0, "duplicates": 12, "failed": 0, "needs_review": 0, "new": 0, "queued": 0, "read": 12, "sent": 0, "skipped_no_text": 0}
$ wc -l /tmp/techproblemo-deliveries.jsonl
6 /tmp/techproblemo-deliveries.jsonl
```

Первый проход сохраняет синтетические материалы, классифицирует непустые и записывает подходящие
карточки в файл. Второй распознаёт все входы как точные повторы и ничего повторно не доставляет.
Это проверка механики, а не оценка качества LLM или live-интеграций.
