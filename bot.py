ltfrom flask import Flask, request
import requests
import os
import json
from threading import Lock

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USERS_FILE = "users.json"
users_lock = Lock()

# Отправка одного сообщения
def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

# Загрузка пользователей
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# Сохранение пользователей
def save_users(user_ids):
    with open(USERS_FILE, "w") as f:
        json.dump(user_ids, f)

# Регистрация
def register_user(user_id):
    with users_lock:
        user_ids = load_users()
        if user_id not in user_ids:
            user_ids.append(user_id)
            save_users(user_ids)

# Отправка всем
def broadcast_message(text):
    user_ids = load_users()
    for user_id in user_ids:
        send_message(user_id, text)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

# Telegram webhook
@app.route(f"/bot{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json

    if not data or "message" not in data:
        return "No message", 400

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    register_user(chat_id)

    if text == "/start":
        welcome = (
            "👋 Привет! Ты успешно подписан на уведомления от Aspro.\n"
            "Теперь ты будешь получать сообщения о новых задачах, поставленных в системе.\n\n"
            "ℹ️ Если бот используется командой, убедись, что каждый сотрудник написал /start."
        )
        send_message(chat_id, welcome)

    return "OK", 200

# Aspro webhook
@app.route("/aspro-webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    if not data:
        return "No data", 400

    task_name = data.get("name", "Без названия")
    project = data.get("project_name", "Без проекта")
    responsible = data.get("responsible_name", "Не назначен")
    url = data.get("link", "https://pirus.aspro.cloud/")

    message = f"📌 <b>Новая задача в Aspro</b>\n" \
              f"📂 Проект: {project}\n" \
              f"📝 Задача: {task_name}\n" \
              f"👤 Ответственный: {responsible}\n" \
              f"🔗 <a href='{url}'>Открыть задачу</a>"

    broadcast_message(message)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
