"""AC-1, AC-2, AC-4: /api/lead, письмо (mock SMTP), GET / (2 экрана + форма)."""
import smtplib

import pytest

from app import app as flask_app
from app import build_message, clean_phone

# --- конфиг для тестов -----------------------------------------------------

BASE_CFG = {
    "SITE_URL": "http://127.0.0.1:5000",
    "AUTHOR_FIO": "Гринина Лилия",
    "TO_EMAIL": "superhumansmm@yandex.ru",
    "TEST_TO_EMAIL": "lily-test@example.com",
    "SMTP_HOST": "smtp.yandex.ru",
    "SMTP_PORT": 465,
    "SMTP_USER": "sender@example.com",
    "SMTP_APP_PASSWORD": "secret",
    "BOT_TOKEN": "",
    "BOT_USERNAME": "",
}


@pytest.fixture()
def client():
    flask_app.config["CFG"] = dict(BASE_CFG)
    return flask_app.test_client()


class FakeSMTP:
    """Перехват smtplib.SMTP_SSL: письма копятся в FakeSMTP.sent, наружу не уходят."""

    sent = []

    def __init__(self, host, port, timeout=None):
        self.host = host
        self.port = port
        self.login_args = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, msg):
        FakeSMTP.sent.append(msg)


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    FakeSMTP.sent = []
    monkeypatch.setattr(smtplib, "SMTP_SSL", FakeSMTP)


# --- валидация телефона ------------------------------------------------------

def test_clean_phone_ok():
    assert clean_phone("+7 (912) 345-67-89") == "79123456789"
    assert clean_phone("89123456789") == "89123456789"
    assert len(clean_phone("+1 202 555 0123")) == 11


def test_clean_phone_bad():
    assert clean_phone("abc") is None
    assert clean_phone("12345") is None
    assert clean_phone("") is None
    assert clean_phone(None) is None


# --- AC-1: письмо уходит и содержит строки по ТЗ ------------------------------

def test_lead_ok_sends_letter(client):
    resp = client.post("/api/lead", json={"name": "Иван Петров", "phone": "+7 (912) 345-67-89"})
    assert resp.status_code == 200
    assert resp.get_json() == {"ok": True}

    assert len(FakeSMTP.sent) == 1
    msg = FakeSMTP.sent[0]
    # получатель: TEST_TO_EMAIL, а не клиентский ящик
    assert msg["To"] == "lily-test@example.com"
    assert msg["From"] == "sender@example.com"
    assert msg["Subject"] == "Новая заявка с сайта http://127.0.0.1:5000"

    body = msg.get_content()
    assert "Новая заявка с сайта http://127.0.0.1:5000" in body
    assert "Автор: Гринина Лилия" in body
    assert "Имя: Иван Петров" in body
    assert "Телефон: +7 (912) 345-67-89" in body
    assert "Время: " in body


def test_build_message_lines_order():
    msg = build_message(BASE_CFG, "Анна", "89990001122")
    lines = msg.get_content().splitlines()
    assert lines[0] == "Новая заявка с сайта http://127.0.0.1:5000"
    assert lines[1] == ""
    assert lines[2] == "Автор: Гринина Лилия"


# --- AC-2: невалидные заявки -> 400, письма нет -------------------------------

@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "phone": "+7 912 345-67-89"},
        {"name": "   ", "phone": "+7 912 345-67-89"},
        {"name": "Иван", "phone": "abc"},
        {"name": "Иван", "phone": ""},
        {"name": "Иван", "phone": "12345"},
        {"name": "И" * 101, "phone": "+7 912 345-67-89"},
        {"name": "Иван"},  # нет телефона
        None,
    ],
)
def test_lead_invalid_400_no_email(client, payload):
    resp = client.post("/api/lead", json=payload)
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False
    assert FakeSMTP.sent == []


# --- AC-4: GET / отдаёт лендинг с двумя экранами и формой ---------------------

def test_index_has_two_screens_and_form(client):
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert 'id="screen-1"' in html
    assert 'id="screen-2"' in html
    assert 'name="name"' in html
    assert 'name="phone"' in html
    assert 'id="leadForm"' in html
