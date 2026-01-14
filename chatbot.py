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
    if source_lang == target_lang:
        return text
    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{target_lang}"
        response = requests.get(url).json()
        return response["responseData"]["translatedText"]
    except:
        return text


def detect_language(text):
    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair=auto|en"
        response = requests.get(url).json()
        lang = response["responseData"].get("matchedLanguage")
        return lang.lower() if lang else "pt"
    except:
        return "pt"


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")

    # 1. Detetar idioma original
    user_lang = detect_language(user_message)

    # 2. Traduzir pergunta para português para comparar com FAQ
    message_pt = translate_text(user_message, user_lang, "pt").lower()

    # 3. Verificar FAQ em português
    for key, answer in faq.items():
        if key in message_pt:
            # 4. Traduzir resposta para a língua original
            translated_answer = translate_text(answer, "pt", user_lang)
            return jsonify({"response": translated_answer})

    # 5. Pergunta nova → enviar para Google Sheets
    requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message})

    fallback = "Pode repetir a sua questão? 😊"
    translated_fallback = translate_text(fallback, "pt", user_lang)

    return jsonify({"response": translated_fallback})


if __name__ == "__main__":
    app.run(debug=True)
