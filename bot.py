"""Telegram-бот: благодарит за регистрацию (SPEC FR-6).

Long polling, только stdlib (urllib) — работает локально и за VPN, публичный URL не нужен.
Запуск:  python bot.py   (нужен BOT_TOKEN в config.json)
"""
import json
import sys
import time
import urllib.request

import config as config_mod

POLL_TIMEOUT = 30
GREET = "Спасибо за регистрацию! Ваша заявка принята — мы скоро свяжемся с вами."
GREET_PERSONAL = "Спасибо, {name}! Ваша заявка принята — мы скоро свяжемся с вами."
FALLBACK = "Спасибо за обращение! Если вы оставили заявку на сайте — мы скоро свяжемся с вами."


def api_url(cfg, method):
    return f"https://api.telegram.org/bot{cfg['BOT_TOKEN']}/{method}"


def api_call(cfg, method, payload=None, timeout=POLL_TIMEOUT + 10):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(api_url(cfg, method), data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def reply_text_for(text):
    """Чистая функция: текст сообщения -> текст ответа (None = не отвечать)."""
    if not isinstance(text, str):
        return None
    text = text.strip()
    if not text:
        return None
    if text.startswith("/start"):
        payload = text[len("/start"):].strip()
        if payload:
            return GREET_PERSONAL.format(name=payload)
        return GREET
    return FALLBACK


def handle_update(update):
    """-> {"chat_id": int, "text": str} | None (чистая функция для тестов)."""
    msg = update.get("message") or {}
    chat = msg.get("chat") or {}
    reply = reply_text_for(msg.get("text"))
    if not reply or not chat.get("id"):
        return None
    return {"chat_id": chat["id"], "text": reply}


def run(cfg):
    if not cfg.get("BOT_TOKEN"):
        raise SystemExit(
            "[bot] BOT_TOKEN не задан. Создай бота у @BotFather, получи токен, "
            "впиши его и BOT_USERNAME в config.json (см. README)."
        )
    offset = 0
    print(f"[bot] слушаю... (@{cfg.get('BOT_USERNAME') or '?'})")
    while True:
        try:
            result = api_call(
                cfg, "getUpdates",
                {"offset": offset, "timeout": POLL_TIMEOUT, "allowed_updates": ["message"]},
            )
            for update in result.get("result", []):
                update_id = update.get("update_id", 0)
                if update_id >= offset:
                    offset = update_id + 1
                reply = handle_update(update)
                if reply:
                    api_call(cfg, "sendMessage", {"chat_id": reply["chat_id"], "text": reply["text"]})
                    print(f"[bot] -> {reply['chat_id']}: {reply['text']}")
        except KeyboardInterrupt:
            print("\n[bot] остановлен")
            return
        except Exception as exc:  # сеть/API — не роняем цикл
            print(f"[bot] ошибка: {exc!r}; повтор через 5 с", file=sys.stderr)
            time.sleep(5)


if __name__ == "__main__":
    run(config_mod.load())
