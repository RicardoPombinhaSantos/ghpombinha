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

def translate_text(text, source_lang, target_lang):
    """Traduz texto usando MyMemory API."""
    url = f"https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{target_lang}"
    response = requests.get(url).json()
    return response["responseData"]["translatedText"]

def detect_language(text):
    """Deteta idioma usando MyMemory (truque simples)."""
    url = f"https://api.mymemory.translated.net/get?q={text}&langpair=auto|en"
    response = requests.get(url).json()
    return response["responseData"]["matchedLanguage"]

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    # Detetar idioma do utilizador
    user_lang = detect_language(user_message)

    # Converter para minúsculas para comparar com FAQ
    user_message_lower = user_message.lower()

    # Verificar FAQ
    for key, answer in faq.items():
        if key in user_message_lower:
            translated_answer = translate_text(answer, "pt", user_lang)
            return jsonify({"response": translated_answer})

    # Pergunta nova → enviar para Google Sheets
    requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message})

    fallback = "Pode repetir a sua questão? 😊"
    translated_fallback = translate_text(fallback, "pt", user_lang)

    return jsonify({"response": translated_fallback})

if __name__ == "__main__":
    app.run(debug=True)
