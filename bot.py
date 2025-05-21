from flask import Flask, request
import requests
import os
import json
from threading import Lock

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USERS_FILE = "users.json"
users_lock = Lock()


def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if keyboard:
        payload["reply_markup"] = json.dumps(keyboard)
    requests.post(url, json=payload)


def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(user_ids):
    with open(USERS_FILE, "w") as f:
        json.dump(user_ids, f)


def register_user(user_id):
    with users_lock:
        user_ids = load_users()
        if user_id not in user_ids:
            user_ids.append(user_id)
            save_users(user_ids)


def broadcast_message(text):
    user_ids = load_users()
    for user_id in user_ids:
        send_message(user_id, text)


@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200


@app.route(f"/bot{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json

    if not data or "message" not in data:
        return "No message", 400

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    register_user(chat_id)

    if text == "/start" or text == "🔔 Подписаться на уведомления":
        welcome = (
            "👋 Привет! Ты успешно подписан на уведомления от Aspro.\n"
            "Теперь ты будешь получать сообщения о новых задачах, поставленных в системе.\n\n"
            "ℹ️ Убедись, что каждый сотрудник тоже нажал кнопку или отправил /start."
        )

        keyboard = {
            "keyboard": [["🔔 Подписаться на уведомления"]],
            "resize_keyboard": True,
            "one_time_keyboard": False
        }

        send_message(chat_id, welcome, keyboard=keyboard)

    return "OK", 200


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
              f"🔗 <a href='{url}'>Открыть задачу</a>"

    broadcast_message(message)
    return "OK", 200


# Установка встроенных команд Telegram
def set_bot_commands():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "start", "description": "Подписаться на уведомления"},
        {"command": "help", "description": "Как работает бот"},
    ]
    response = requests.post(url, json={"commands": commands})
    print("✅ Команды обновлены:", response.status_code, response.text)


# Для локального запуска
if __name__ == "__main__":
    set_bot_commands()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# Для продакшна (Render / Railway)
else:
    set_bot_commands()
