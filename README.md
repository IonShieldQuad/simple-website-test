# simple-website-test — лендинг 2 экрана + Telegram-бот + уведомления на почту

Демо-лендинг по ТЗ: два экрана, форма заявки (имя + телефон), письмо-уведомление
на `superhumansmm@yandex.ru` по заданному шаблону, редирект пользователя после
отправки в Telegram-бота, который благодарит за регистрацию.

Спека и acceptance criteria: [SPEC.md](SPEC.md).

## Состав

| Файл | Назначение |
|---|---|
| `app.py` | Flask: GET / (лендинг), POST /api/lead (валидация + SMTP-письмо) |
| `bot.py` | Telegram-бот: long polling, благодарность на /start (с именем и без) |
| `config.py` | Чтение config.json + env-переменных (env приоритетнее) |
| `templates/index.html` | Лендинг: 2 экрана, тёмная тема, JS-валидация, редирект в бота |
| `tests/` | 17 pytest: письмо через mock SMTP, валидация, бот, страница |
| `config.example.json` | Шаблон конфига (копируй в `config.json`) |
| `Procfile` | Для деплоя на Render (`gunicorn app:app`) |

## Быстрый старт (Windows)

```bash
python -m venv .venv --system-site-packages
.venv/Scripts/python -m pip install -r requirements.txt
cp config.example.json config.json   # затем заполни config.json
.venv/Scripts/python app.py          # сайт: http://127.0.0.1:5000
.venv/Scripts/python bot.py          # бот (отдельный терминал)
```

Тесты: `.venv/Scripts/python -m pytest -q`

## Что заполнить в config.json

| Ключ | Откуда берётся |
|---|---|
| `SITE_URL` | адрес, который попадёт в письмо («Новая заявка с сайта …») |
| `AUTHOR_FIO` | «Автор: …» в письме |
| `TO_EMAIL` | `superhumansmm@yandex.ru` (получатель) |
| `TEST_TO_EMAIL` | если заполнен — письма уходят сюда вместо TO_EMAIL (для отладки) |
| `SMTP_USER` / `SMTP_APP_PASSWORD` | твой яндекс-логин и **пароль приложения** |
| `BOT_TOKEN` / `BOT_USERNAME` | токен и юзернейм бота |

### Пароль приложения Yandex (для SMTP)
1. id.yandex.ru → Безопасность → включи двухфакторную аутентификацию (если ещё нет).
2. Там же → «Пароли приложений» → создать для «Почты» → вписать 16-символьный пароль
   в `SMTP_APP_PASSWORD` (обычный пароль от почты не подойдёт).
3. SMTP: `smtp.yandex.ru:465`, SSL — уже в `config.example.json` по умолчанию.

### Бот
1. У @BotFather: `/newbot` → получишь токен и юзернейм.
2. Токен → `BOT_TOKEN`, юзернейм без `@` → `BOT_USERNAME`.
3. `python bot.py` — бот слушает; после отправки формы сайт редиректит на
   `t.me/<BOT_USERNAME>?start=<транслит-имя>` — бот ответит «Спасибо, <имя>! …».

## Как проверить письмо до сдачи
1. Заполни SMTP-креды.
2. Впиши свой ящик в `TEST_TO_EMAIL` — все письма будут уходить тебе, а не клиенту.
3. Отправь форму → проверь письмо (тема: «Новая заявка с сайта …», тело: Автор/Имя/Телефон).
4. Перед сдачей очисти `TEST_TO_EMAIL`.

## Деплой (когда понадобится публичный адрес)
- **Render (бесплатно):** заведи репозиторий на GitHub → New Web Service → указать репо;
  Build `pip install -r requirements.txt`, Start `gunicorn app:app`.
  Секреты — через Environment Variables на дашборде Render (те же ключи, что в config.json;
  env имеет приоритет). Бот — вторым Web Service'ом (`python bot.py`) или локально.
  Free-инстансы засыпают после ~15 мин простоя — держать живым помогает бесплатный
  пинг (UptimeRobot) раз в 10–14 минут.
- **Локальная демонстрация:** просто покажи `http://127.0.0.1:5000` — всё работает без
  публичного хостинга, пока ПК включён.
