from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import deepl
import os

app = Flask(__name__)
CORS(app)

# API KEY do DeepL (ideal: variável de ambiente)
DEEPL_KEY = os.getenv("DEEPL_API_KEY", "AQUI_A_TUA_API_KEY")
translator = deepl.Translator(DEEPL_KEY)

faq = {
    "preço": "Os quartos começam a partir de 60€ por noite.",
    "localização": "Estamos em Leiria, a 10 minutos do centro.",
    "check-in": "O check-in é das 14h às 20h.",
    "check-out": "O check-out é até às 11h."
}

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbxb_0oe7Q8L8_Un01bZoTIiJIw0ndYIgo9j-9mx7VjbZFyZKXW8GxoPj9fGI-6QnCslOw/exec"

def translate_text(text, target_lang):
    """Traduz texto usando DeepL."""
    result = translator.translate_text(text, target_lang=target_lang)
    return result.text

def detect_language(text):
    """Deteta idioma usando DeepL."""
    # DeepL devolve o idioma original ao traduzir
    result = translator.translate_text(text, target_lang="EN-US")
    return result.detected_source_lang.lower()

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
            translated_answer = translate_text(answer, user_lang)
            return jsonify({"response": translated_answer})

    # Pergunta nova → enviar para Google Sheets
    requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message})

    fallback = "Pode repetir a sua questão? 😊"
    translated_fallback = translate_text(fallback, user_lang)

    return jsonify({"response": translated_fallback})

if __name__ == "__main__":
    app.run(debug=True)

