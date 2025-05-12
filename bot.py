from flask import Flask, request
import requests
import os
import json
from threading import Lock

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USERS_FILE = "users.json"
users_lock = Lock()

# Загрузка пользователей из файла
def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# Сохранение пользователей в файл
def save_users(user_ids):
    with open(USERS_FILE, "w") as f:
        json.dump(user_ids, f)

# Добавление нового пользователя
def register_user(user_id):
    with users_lock:
        user_ids = load_users()
        if user_id not in user_ids:
            user_ids.append(user_id)
            save_users(user_ids)

# Отправка сообщения всем пользователям
def broadcast_message(text):
    user_ids = load_users()
    for user_id in user_ids:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": user_id,
            "text": text,
            "parse_mode": "HTML"
        }
        requests.post(url, json=payload)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

# Вебхук от Telegram
@app.route(f"/bot{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    data = request.json
    print("📩 Получен вебхук от Aspro:", data)
    if not data or "message" not in data:
        return "No message", 400

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    # Регистрация пользователя
    register_user(chat_id)

    # Ответ на /start
    if text == "/start":
        send_text = "✅ Вы зарегистрированы для получения уведомлений о задачах из Aspro."
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      json={"chat_id": chat_id, "text": send_text})
    return "OK", 200

# Вебхук от Aspro
@app.route("/aspro-webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    if not data:
        return "No data", 400

    task_name = data.get("name", "Без названия")
    project = data.get("project_name", "Без проекта")
    responsible = data.get("responsible_name", "Не назначен")
    url = data.get("link", "#")

    message = f"📌 <b>Новая задача в Aspro</b>\n" \
              f"📂 Проект: {project}\n" \
              f"📝 Задача: {task_name}\n" \
              f"👤 Ответственный: {responsible}\n" \
              f"🔗 <a href='{url}'>Открыть задачу</a>"

    broadcast_message(message)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
