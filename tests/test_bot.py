"""AC-3: bot-handler — /start с payload и без, заглушка на прочее."""
from bot import handle_update, reply_text_for


def test_start_with_payload_personal_thanks():
    update = {"message": {"chat": {"id": 42}, "text": "/start Ivan"}}
    reply = handle_update(update)
    assert reply == {"chat_id": 42, "text": "Спасибо, Ivan! Ваша заявка принята — мы скоро свяжемся с вами."}


def test_start_without_payload_generic_thanks():
    reply = handle_update({"message": {"chat": {"id": 1}, "text": "/start"}})
    assert "Спасибо за регистрацию" in reply["text"]


def test_plain_message_gets_fallback():
    reply = reply_text_for("привет")
    assert "Спасибо за обращение" in reply


def test_no_message_no_reply():
    assert handle_update({"message": {"chat": {"id": 1}}}) is None
    assert handle_update({}) is None
    assert reply_text_for("") is None
