from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("7238683695:AAEetDQmRr3yxooQuwMi7WIIOghvL38SUVU")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_USER_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, json=payload)

@app.route("/", methods=["GET"])
def home():
    return "Bot is running!", 200

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

    send_telegram_message(message)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
