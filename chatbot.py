from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

faq = {
    "preço": "Os quartos começam a partir de 60€ por noite.",
    "localização": "Estamos em Leiria, a 10 minutos do centro.",
    "check-in": "O check-in é das 14h às 20h.",
    "check-out": "O check-out é até às 11h."
}

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbxb_0oe7Q8L8_Un01bZoTIiJIw0ndYIgo9j-9mx7VjbZFyZKXW8GxoPj9fGI-6QnCslOw/exec"

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()

    for key, answer in faq.items():
        if key in user_message:
            return jsonify({"response": answer})

    # Enviar pergunta nova para Google Sheets
    requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message})

    return jsonify({"response": "Pode repetir a sua questão? 😊"})

if __name__ == "__main__":
    app.run(debug=True)


