"""Flask: лендинг (GET /) + приём заявок (POST /api/lead) + SMTP-уведомление.

Спека: SPEC.md FR-1..FR-5, §11 AC-1/AC-2/AC-4.
"""
import smtplib
from datetime import datetime
from email.message import EmailMessage
from zoneinfo import ZoneInfo

from flask import Flask, current_app, jsonify, render_template, request

import config as config_mod

app = Flask(__name__)
app.config["CFG"] = config_mod.load()


class ConfigMissing(Exception):
    """SMTP-креды не заполнены — письмо отправить нельзя."""


def clean_phone(raw):
    """-> строка из 10..15 цифр или None."""
    if not isinstance(raw, str):
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    return digits if 10 <= len(digits) <= 15 else None


def validate_lead(payload):
    """-> (name, phone_raw, None) при успехе, (None, None, error_code) при ошибке."""
    if not isinstance(payload, dict):
        return None, None, "invalid_json"
    name = (payload.get("name") or "").strip()
    if not name or len(name) > 100:
        return None, None, "invalid_name"
    phone = (payload.get("phone") or "").strip()
    if clean_phone(phone) is None:
        return None, None, "invalid_phone"
    return name, phone, None


def build_message(cfg, name, phone):
    """Письмо ровно по ТЗ (SPEC FR-5)."""
    site = cfg["SITE_URL"]
    now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M")
    body = "\n".join(
        [
            f"Новая заявка с сайта {site}",
            "",
            f"Автор: {cfg['AUTHOR_FIO']}",
            "",
            f"Имя: {name}",
            f"Телефон: {phone}",
            f"Время: {now}",
        ]
    )
    msg = EmailMessage()
    msg["Subject"] = f"Новая заявка с сайта {site}"
    msg["From"] = cfg["SMTP_USER"]
    msg["To"] = cfg["TEST_TO_EMAIL"] or cfg["TO_EMAIL"]
    msg.set_content(body)
    return msg


def send_email(cfg, msg):
    """SMTP_SSL (Yandex: 465). Кидает ConfigMissing / smtplib / OSError."""
    user = cfg["SMTP_USER"]
    secret = cfg["SMTP_APP_PASSWORD"]
    if not user or not secret:
        raise ConfigMissing("SMTP_USER / SMTP_APP_PASSWORD не заполнены — см. README")
    with smtplib.SMTP_SSL(cfg["SMTP_HOST"], int(cfg["SMTP_PORT"]), timeout=15) as server:
        server.login(user, secret)
        server.send_message(msg)


@app.get("/")
def index():
    cfg = current_app.config["CFG"]
    return render_template(
        "index.html",
        bot_username=cfg.get("BOT_USERNAME") or "",
        site_url=cfg.get("SITE_URL") or "",
    )


@app.post("/api/lead")
def api_lead():
    cfg = current_app.config["CFG"]
    try:
        payload = request.get_json(silent=True)
    except Exception:
        payload = None
    name, phone, err = validate_lead(payload)
    if err:
        return jsonify(ok=False, error=err), 400
    phone = (payload.get("phone") or "").strip()
    try:
        send_email(cfg, build_message(cfg, name, phone))
    except ConfigMissing:
        current_app.logger.error("api_lead: SMTP не настроен (пустые SMTP_USER/SMTP_APP_PASSWORD)")
        return jsonify(ok=False, error="smtp_not_configured"), 502
    except (smtplib.SMTPException, OSError) as exc:
        current_app.logger.error("api_lead: SMTP send failed: %r", exc)
        return jsonify(ok=False, error="smtp"), 502
    current_app.logger.info("api_lead: письмо отправлено -> %s", cfg["TEST_TO_EMAIL"] or cfg["TO_EMAIL"])
    return jsonify(ok=True)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
