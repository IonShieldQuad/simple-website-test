"""Толерантный читатель конфига: config.json + env-переменные (env приоритетнее).

Неизвестные ключи в config.json игнорируются, отсутствующие берутся из DEFAULTS.
Обязательные для конкретной функции проверяются в момент её вызова (app/bot),
а не при импорте — чтобы dev/тесты работали без секретов.
"""
import json
import os
from pathlib import Path

DEFAULTS = {
    "SITE_URL": "http://127.0.0.1:5000",
    "AUTHOR_FIO": "Гринина Лилия",
    "TO_EMAIL": "superhumansmm@yandex.ru",
    "TEST_TO_EMAIL": "",
    "SMTP_HOST": "smtp.yandex.ru",
    "SMTP_PORT": 465,
    "SMTP_USER": "",
    "SMTP_APP_PASSWORD": "",
    "BOT_TOKEN": "",
    "BOT_USERNAME": "",
}


def load(path=None):
    cfg_path = Path(path) if path else Path(__file__).resolve().parent / "config.json"
    cfg = dict(DEFAULTS)
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            raise SystemExit(f"[config] не могу прочитать {cfg_path.name}: {e}") from e
        if not isinstance(data, dict):
            raise SystemExit(f"[config] {cfg_path.name}: ожидался JSON-объект")
        for key in DEFAULTS:
            value = data.get(key)
            if value is not None:
                cfg[key] = value
    for key in DEFAULTS:  # env override
        value = os.environ.get(key)
        if value:
            cfg[key] = value
    return cfg
