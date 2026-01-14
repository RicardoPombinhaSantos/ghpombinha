from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import difflib

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# FAQ TEMÁTICO MULTILINGUE (respostas em PT)
# -----------------------------------------
faq = {
    "preço": {
        "keywords": [
            "preço", "price", "prix", "precio", "prezzo", "preis",
            "quanto custa", "how much", "cost", "costo", "costo", "kosten"
        ],
        "answer": "Os quartos começam a partir de 60€ por noite."
    },
    "localização": {
        "keywords": [
            "localização", "location", "ubicación", "emplacement", "lage",
            "onde fica", "where are you", "onde estão", "onde é", "where is"
        ],
        "answer": "Estamos em Leiria, a 10 minutos do centro."
    },
    "check-in": {
        "keywords": [
            "check-in", "check in", "hora de entrada", "arrival time",
            "arrivée", "llegada", "ankunft", "time to check in"
        ],
        "answer": "O check-in é das 14h às 20h."
    },
    "check-out": {
        "keywords": [
            "check-out", "check out", "hora de saída", "departure time",
            "départ", "salida", "abreise", "time to check out"
        ],
        "answer": "O check-out é até às 11h."
    },
    "nazaré": {
        "keywords": [
            "nazaré", "nazare", "big waves", "ondas grandes", "praia da nazaré",
            "nazaré beach", "plage nazaré", "playa nazaré"
        ],
        "answer": "A Nazaré fica a cerca de 30 minutos e é famosa pelas ondas gigantes na Praia do Norte."
    },
    "o que ver": {
        "keywords": [
            "o que ver", "what to see", "things to see", "things to do",
            "sightseeing", "tourism", "qué ver", "cosa vedere", "was sehen",
            "visitar", "visit", "places to visit"
        ],
        "answer": "Perto de Leiria pode visitar o castelo, o Santuário de Fátima, o Mosteiro da Batalha e São Pedro de Moel."
    },
    "restaurantes": {
        "keywords": [
            "restaurantes", "restaurant", "restaurants", "onde comer", "where to eat",
            "donde comer", "où manger", "wo essen", "ristoranti", "gastronomia"
        ],
        "answer": "Recomendamos o restaurante 'O Casarão', 'Taberna do Terreiro' e 'Mata Bicho' em Leiria."
    },
    "estacionamento": {
        "keywords": [
            "estacionamento", "parking", "parque", "aparcamiento",
            "parcheggio", "parkplatz", "car park", "park"
        ],
        "answer": "Temos estacionamento gratuito junto à propriedade."
    },
    "wifi": {
        "keywords": [
            "wifi", "wi-fi", "internet", "net", "wi fi", "wiﬁ", "wi fi password",
            "internet access"
        ],
        "answer": "Disponibilizamos Wi-Fi gratuito em toda a propriedade."
    },
    "animais": {
        "keywords": [
            "animais", "pets", "cães", "dogs", "mascotas", "animaux",
            "pet friendly", "animali", "haustiere"
        ],
        "answer": "Aceitamos animais de estimação mediante pedido prévio."
    },
    "pequeno-almoço": {
        "keywords": [
            "pequeno-almoço", "pequeno almoço", "breakfast", "desayuno",
            "petit déjeuner", "frühstück", "colazione", "morning meal"
        ],
        "answer": "O pequeno-almoço está incluído em algumas tarifas. Confirme na sua reserva ou contacte-nos."
    },
    "transportes": {
        "keywords": [
            "transportes", "transporte", "bus", "autocarro", "ônibus",
            "train", "comboio", "gare", "estação", "station",
            "how to get", "como chegar"
        ],
        "answer": "Leiria tem ligações de autocarro e comboio. A partir da estação, pode chegar de táxi ou transporte próprio."
    },
    "praias": {
        "keywords": [
            "praias", "beach", "beaches", "playa", "plage", "strand",
            "sea", "mar", "coast", "litoral"
        ],
        "answer": "As praias mais próximas são São Pedro de Moel, Vieira e Nazaré."
    },
    "pagamento": {
        "keywords": [
            "pagamento", "payment", "pay", "pagar", "tarifa", "tariff",
            "card", "cartão", "credit card", "cash", "dinheiro", "contado"
        ],
        "answer": "Aceitamos pagamento em cartão de crédito, débito e numerário no local."
    },
    "política de cancelamento": {
        "keywords": [
            "cancelamento", "cancellation", "cancel policy", "política de cancelamento",
            "cancelar reserva", "cancel booking"
        ],
        "answer": "A política de cancelamento varia consoante a tarifa. Verifique as condições da sua reserva."
    },
    "quartos": {
        "keywords": [
            "quartos", "rooms", "room types", "tipos de quarto",
            "single room", "double room", "twin", "suite"
        ],
        "answer": "Temos vários tipos de quarto, incluindo duplos, twin e familiares. Contacte-nos para disponibilidade."
    },
    "capacidade": {
        "keywords": [
            "capacidade", "capacity", "people", "pessoas", "guests",
            "hóspedes", "ocupação", "occupancy"
        ],
        "answer": "Alguns quartos acomodam até 2 pessoas, outros até 4. Indique-nos o número de hóspedes."
    }
}

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbxb_0oe7Q8L8_Un01bZoTIiJIw0ndYIgo9j-9mx7VjbZFyZKXW8GxoPj9fGI-6QnCslOw/exec"

# -----------------------------------------
# Tradução MyMemory
# -----------------------------------------
def translate_text(text, source_lang, target_lang):
    if source_lang == target_lang:
        return text
    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair={source_lang}|{target_lang}"
        response = requests.get(url).json()
        return response["responseData"]["translatedText"]
    except:
        return text

# -----------------------------------------
# Deteção de idioma
# -----------------------------------------
def detect_language(text):
    try:
        url = f"https://api.mymemory.translated.net/get?q={text}&langpair=auto|en"
        response = requests.get(url).json()
        lang = response["responseData"].get("matchedLanguage")
        return lang.lower() if lang else "pt"
    except:
        return "pt"

# -----------------------------------------
# Matching melhorado (exato + fuzzy)
# -----------------------------------------
def find_best_faq_match(user_message_lower):
    # 1. Matching direto por substring em qualquer keyword
    for topic, data in faq.items():
        for kw in data["keywords"]:
            if kw in user_message_lower:
                return data["answer"]

    # 2. Fuzzy matching simples com difflib (sem libs externas)
    words = user_message_lower.split()
    all_keywords = []
    mapping = {}

    for topic, data in faq.items():
        for kw in data["keywords"]:
            all_keywords.append(kw)
            mapping[kw] = data["answer"]

    for w in words:
        close = difflib.get_close_matches(w, all_keywords, n=1, cutoff=0.8)
        if close:
            return mapping[close[0]]

    return None

# -----------------------------------------
# Endpoint principal
# -----------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    user_lang = detect_language(user_message)
    user_message_lower = user_message.lower()

    answer_pt = find_best_faq_match(user_message_lower)

    if answer_pt:
        translated_answer = translate_text(answer_pt, "pt", user_lang)
        return jsonify({"response": translated_answer})

    # Pergunta nova → enviar para Google Sheets
    requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message})

    fallback = "Pode repetir a sua questão? 😊"
    translated_fallback = translate_text(fallback, "pt", user_lang)
    return jsonify({"response": translated_fallback})


if __name__ == "__main__":
    app.run(debug=True)
