from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import difflib
import urllib.parse
import os

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# FAQ TEMÁTICO MULTILINGUE (respostas em PT)
# -----------------------------------------
faq = {
    "preço": {
        "keywords": [
            "preço", "price", "prix", "precio", "prezzo", "preis",
            "quanto custa", "how much", "cost", "costo", "kosten"
        ],
        "answer": "Os quartos começam a partir de 60€ por noite."
    },
    "localizacao": {
        "keywords": [
            "localização", "location", "ubicación", "emplacement", "lage",
            "onde fica", "where are you", "onde estão", "onde é", "where is",
            "where", "located"
        ],
        "answer": "Estamos na Nazaré, a 5 minutos do centro de carro e a 30 minutos a pé."
    },
    "check-in": {
        "keywords": [
            "check-in", "check in", "hora de entrada", "arrival time",
            "arrivée", "llegada", "ankunft", "time to check in"
        ],
        "answer": "O check-in é das 15h às 21h."
    },
    "check-out": {
        "keywords": [
            "check-out", "check out", "hora de saída", "departure time",
            "départ", "salida", "abreise", "time to check out"
        ],
        "answer": "O check-out é até às 11:30h."
    },
    "nazare": {
        "keywords": [
            "nazaré", "nazare", "big waves", "ondas grandes", "praia da nazaré",
            "nazaré beach", "plage nazaré", "playa nazaré"
        ],
        "answer": "A Nazaré é famosa pelas ondas gigantes na Praia do Norte, estamos a 5 minutos de carro das ondas."
    },
    "o que ver": {
        "keywords": [
            "o que ver", "what to see", "things to see", "things to do",
            "sightseeing", "tourism", "qué ver", "cosa vedere", "was sehen",
            "visitar", "visit", "places to visit"
        ],
        "answer": "Perto da Nazaré pode visitar o castelo, o Santuário de Fátima, o Mosteiro da Batalha, São Pedro de Moel e Alcobaça."
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
    "politica de cancelamento": {
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
# TRADUÇÕES COMPLETAS
# -----------------------------------------
MANUAL_ANSWER_TRANSLATIONS = {
    "Os quartos começam a partir de 60€ por noite.": {
        "en": "Rooms start at €60 per night.",
        "es": "Las habitaciones comienzan desde 60€ por noche.",
        "fr": "Les chambres commencent à partir de 60€ par nuit.",
        "it": "Le camere partono da 60€ a notte.",
        "de": "Die Zimmer beginnen bei 60€ pro Nacht."
    },
    "Estamos na Nazaré, a 5 minutos do centro de carro e a 30 minutos a pé.": {
        "en": "We are in Nazaré, 5 minutes from the center by car and 30 minutes on foot.",
        "es": "Estamos en Nazaré, a 5 minutos del centro en coche y 30 minutos a pie.",
        "fr": "Nous sommes à Nazaré, à 5 minutes du centre en voiture et 30 minutes à pied.",
        "it": "Siamo a Nazaré, a 5 minuti dal centro in auto e 30 minuti a piedi.",
        "de": "Wir sind in Nazaré, 5 Minuten vom Zentrum mit dem Auto und 30 Minuten zu Fuß."
    },
    "O check-in é das 15h às 21h.": {
        "en": "Check-in is from 3:00 PM to 9:00 PM.",
        "es": "El check-in es de 15:00 a 21:00.",
        "fr": "L'enregistrement est de 15h à 21h.",
        "it": "Il check-in è dalle 15:00 alle 21:00.",
        "de": "Der Check-in ist von 15:00 bis 21:00 Uhr."
    },
    "O check-out é até às 11:30h.": {
        "en": "Check-out is until 11:30 AM.",
        "es": "El check-out es hasta las 11:30.",
        "fr": "Le départ est jusqu'à 11h30.",
        "it": "Il check-out è entro le 11:30.",
        "de": "Der Check-out ist bis 11:30 Uhr."
    },
    "A Nazaré é famosa pelas ondas gigantes na Praia do Norte, estamos a 5 minutos de carro das ondas.": {
        "en": "Nazaré is famous for the giant waves at Praia do Norte, we are 5 minutes by car from the waves.",
        "es": "Nazaré es famosa por las olas gigantes en Praia do Norte, estamos a 5 minutos en coche de las olas.",
        "fr": "Nazaré est célèbre pour les vagues géantes à Praia do Norte, nous sommes à 5 minutes en voiture des vagues.",
        "it": "Nazaré è famosa per le onde giganti a Praia do Norte, siamo a 5 minuti di auto dalle onde.",
        "de": "Nazaré ist berühmt für die riesigen Wellen am Praia do Norte, wir sind 5 Minuten mit dem Auto von den Wellen entfernt."
    },
    "Perto da Nazaré pode visitar o castelo, o Santuário de Fátima, o Mosteiro da Batalha, São Pedro de Moel e Alcobaça.": {
        "en": "Near Nazaré you can visit the castle, the Sanctuary of Fátima, the Batalha Monastery, São Pedro de Moel and Alcobaça.",
        "es": "Cerca de Nazaré puede visitar el castillo, el Santuario de Fátima, el Monasterio de Batalha, São Pedro de Moel y Alcobaça.",
        "fr": "Près de Nazaré, vous pouvez visiter le château, le Sanctuaire de Fátima, le Monastère de Batalha, São Pedro de Moel et Alcobaça.",
        "it": "Vicino a Nazaré potete visitare il castello, il Santuario di Fátima, il Monastero di Batalha, São Pedro de Moel e Alcobaça.",
        "de": "In der Nähe von Nazaré können Sie die Burg, das Heiligtum von Fátima, das Kloster Batalha, São Pedro de Moel und Alcobaça besuchen."
    },
    "Recomendamos o restaurante 'O Casarão', 'Taberna do Terreiro' e 'Mata Bicho' em Leiria.": {
        "en": "We recommend the restaurants 'O Casarão', 'Taberna do Terreiro' and 'Mata Bicho' in Leiria.",
        "es": "Recomendamos los restaurantes 'O Casarão', 'Taberna do Terreiro' y 'Mata Bicho' en Leiria.",
        "fr": "Nous recommandons les restaurants 'O Casarão', 'Taberna do Terreiro' et 'Mata Bicho' à Leiria.",
        "it": "Consigliamo i ristoranti 'O Casarão', 'Taberna do Terreiro' e 'Mata Bicho' a Leiria.",
        "de": "Wir empfehlen die Restaurants 'O Casarão', 'Taberna do Terreiro' und 'Mata Bicho' in Leiria."
    },
    "Temos estacionamento gratuito junto à propriedade.": {
        "en": "We have free parking next to the property.",
        "es": "Tenemos aparcamiento gratuito junto a la propiedad.",
        "fr": "Nous disposons d'un parking gratuit à côté de la propriété.",
        "it": "Abbiamo parcheggio gratuito accanto alla struttura.",
        "de": "Wir haben einen kostenlosen Parkplatz neben der Unterkunft."
    },
    "Disponibilizamos Wi-Fi gratuito em toda a propriedade.": {
        "en": "We provide free Wi-Fi throughout the property.",
        "es": "Disponemos de Wi-Fi gratuito en toda la propiedad.",
        "fr": "Nous proposons le Wi-Fi gratuit dans toute la propriété.",
        "it": "Forniamo Wi-Fi gratuito in tutta la struttura.",
        "de": "Wir bieten kostenloses WLAN auf dem gesamten Gelände."
    },
    "Aceitamos animais de estimação mediante pedido prévio.": {
        "en": "We accept pets upon prior request.",
        "es": "Aceptamos mascotas bajo petición previa.",
        "fr": "Nous acceptons les animaux sur demande préalable.",
        "it": "Accettiamo animali su richiesta preventiva.",
        "de": "Haustiere sind auf Anfrage erlaubt."
    },
    "O pequeno-almoço está incluído em algumas tarifas. Confirme na sua reserva ou contacte-nos.": {
        "en": "Breakfast is included in some rates. Please check your booking or contact us.",
        "es": "El desayuno está incluido en algunas tarifas. Confirme en su reserva o contáctenos.",
        "fr": "Le petit-déjeuner est inclus dans certains tarifs. Vérifiez votre réservation ou contactez-nous.",
        "it": "La colazione è inclusa in alcune tariffe. Controlla la tua prenotazione o contattaci.",
        "de": "Frühstück ist in einigen Tarifen enthalten. Prüfen Sie Ihre Buchung oder kontaktieren Sie uns."
    },
    "Leiria tem ligações de autocarro e comboio. A partir da estação, pode chegar de táxi ou transporte próprio.": {
        "en": "Leiria has bus and train connections. From the station you can get here by taxi or private transport.",
        "es": "Leiria tiene conexiones de autobús y tren. Desde la estación puede llegar en taxi o transporte propio.",
        "fr": "Leiria dispose de liaisons en bus et en train. Depuis la gare, vous pouvez venir en taxi ou en transport privé.",
        "it": "Leiria ha collegamenti in autobus e treno. Dalla stazione si può arrivare in taxi o con mezzo proprio.",
        "de": "Leiria hat Bus- und Zugverbindungen. Vom Bahnhof erreichen Sie uns mit Taxi oder eigenem Fahrzeug."
    },
    "As praias mais próximas são São Pedro de Moel, Vieira e Nazaré.": {
        "en": "The nearest beaches are São Pedro de Moel, Vieira and Nazaré.",
        "es": "Las playas más cercanas son São Pedro de Moel, Vieira y Nazaré.",
        "fr": "Les plages les plus proches sont São Pedro de Moel, Vieira et Nazaré.",
        "it": "Le spiagge più vicine sono São Pedro de Moel, Vieira e Nazaré.",
        "de": "Die nächstgelegenen Strände sind São Pedro de Moel, Vieira und Nazaré."
    },
    "Aceitamos pagamento em cartão de crédito, débito e numerário no local.": {
        "en": "We accept payment by credit card, debit card and cash on site.",
        "es": "Aceptamos pago con tarjeta de crédito, débito y efectivo en el lugar.",
        "fr": "Nous acceptons les paiements par carte de crédit, carte de débit et en espèces sur place.",
        "it": "Accettiamo pagamenti con carta di credito, carta di debito e contanti in loco.",
        "de": "Wir akzeptieren Zahlungen per Kreditkarte, Debitkarte und bar vor Ort."
    },
    "A política de cancelamento varia consoante a tarifa. Verifique as condições da sua reserva.": {
        "en": "The cancellation policy varies by rate. Please check your booking conditions.",
        "es": "La política de cancelación varía según la tarifa. Verifique las condiciones de su reserva.",
        "fr": "La politique d'annulation varie selon le tarif. Vérifiez les conditions de votre réservation.",
        "it": "La politica di cancellazione varia in base alla tariffa. Controlla le condizioni della tua prenotazione.",
        "de": "Die Stornierungsbedingungen variieren je nach Tarif. Prüfen Sie die Bedingungen Ihrer Buchung."
    },
    "Temos vários tipos de quarto, incluindo duplos, twin e familiares. Contacte-nos para disponibilidade.": {
        "en": "We have several room types, including doubles, twins and family rooms. Contact us for availability.",
        "es": "Tenemos varios tipos de habitación, incluidos dobles, twin y familiares. Contáctenos para disponibilidad.",
        "fr": "Nous avons plusieurs types de chambres, y compris doubles, twin et familiales. Contactez-nous pour la disponibilité.",
        "it": "Abbiamo diversi tipi di camere, tra cui doppie, twin e familiari. Contattaci per disponibilità.",
        "de": "Wir haben verschiedene Zimmertypen, darunter Doppel-, Twin- und Familienzimmer. Kontaktieren Sie uns für Verfügbarkeit."
    },
    "Alguns quartos acomodam até 2 pessoas, outros até 4. Indique-nos o número de hóspedes.": {
        "en": "Some rooms accommodate up to 2 people, others up to 4. Please tell us the number of guests.",
        "es": "Algunas habitaciones acomodan hasta 2 personas, otras hasta 4. Indíquenos el número de huéspedes.",
        "fr": "Certaines chambres peuvent accueillir jusqu'à 2 personnes, d'autres jusqu'à 4. Indiquez-nous le nombre de personnes.",
        "it": "Alcune camere ospitano fino a 2 persone, altre fino a 4. Indicateci il numero di ospiti.",
        "de": "Einige Zimmer bieten Platz für bis zu 2 Personen, andere bis zu 4. Teilen Sie uns die Anzahl der Gäste mit."
    },
    "Pode repetir a sua questão? 😊": {
        "en": "Could you repeat your question? 😊",
        "es": "¿Puede repetir su pregunta? 😊",
        "fr": "Pouvez-vous répéter votre question? 😊",
        "it": "Può ripetere la sua domanda? 😊",
        "de": "Könnten Sie Ihre Frage wiederholen? 😊"
    }
}

# -----------------------------------------
# Keywords ambíguas (que existem em vários idiomas)
# -----------------------------------------
AMBIGUOUS_KEYWORDS = {"check-in", "check in", "check-out", "check out", "wifi", "wi-fi", "internet"}

# -----------------------------------------
# Inferir idioma a partir da keyword
# -----------------------------------------
LANG_HINTS = {
    "en": {"price", "location", "how", "what", "where", "room", "rooms", "breakfast", "parking", "arrival", "departure"},
    "es": {"precio", "donde", "comer", "desayuno", "playa", "ubicación", "llegada", "salida"},
    "fr": {"prix", "où", "plage", "arrivée", "départ", "emplacement"},
    "it": {"prezzo", "colazione", "dove", "cosa"},
    "de": {"preis", "wo", "frühstück", "parkplatz", "ankunft", "abreise", "lage"}
}

def infer_lang_from_keyword(kw):
    k = kw.lower()
    for code, hints in LANG_HINTS.items():
        for h in hints:
            if h in k:
                return code
    if any(ch in k for ch in "ãáâàçõéêíóú"):
        return "pt"
    return None

# -----------------------------------------
# Detecção de idioma pela frase completa
# -----------------------------------------
def detect_language_from_sentence(text):
    """Detecta o idioma analisando a frase completa"""
    if not text or not text.strip():
        return "pt"
    
    lower = text.lower()
    
    # Palavras fortes por idioma
    pt_indicators = ["é", "são", "que", "qual", "onde", "quando", "quanto", "a que horas", "às", "das"]
    en_indicators = ["is", "are", "what", "when", "where", "how", "at what time", "the"]
    es_indicators = ["es", "son", "qué", "cuál", "dónde", "cuándo", "a qué hora", "las"]
    fr_indicators = ["est", "sont", "quel", "quelle", "où", "quand", "à quelle heure", "les"]
    de_indicators = ["ist", "sind", "was", "wo", "wann", "um wie viel uhr", "die"]
    
    # Contar indicadores
    scores = {
        "pt": sum(1 for w in pt_indicators if w in lower),
        "en": sum(1 for w in en_indicators if w in lower),
        "es": sum(1 for w in es_indicators if w in lower),
        "fr": sum(1 for w in fr_indicators if w in lower),
        "de": sum(1 for w in de_indicators if w in lower)
    }
    
    # Retornar o idioma com mais pontos
    max_lang = max(scores, key=scores.get)
    return max_lang if scores[max_lang] > 0 else "pt"

# -----------------------------------------
# Tradução com fallback manual
# -----------------------------------------
def translate_text(text, source_lang, target_lang):
    if not text or source_lang == target_lang:
        return text
    
    # Tentar primeiro o dicionário manual
    manual = MANUAL_ANSWER_TRANSLATIONS.get(text.strip())
    if manual:
        code = target_lang.lower()[:2]
        return manual.get(code, text)
    
    return text

# -----------------------------------------
# Matching de FAQ
# -----------------------------------------
def find_best_faq_match(user_message, user_message_lower):
    """Retorna (resposta_pt, idioma_detectado)"""
    matched_keyword = None
    matched_answer = None
    
    # 1. Match direto por substring
    for topic, data in faq.items():
        for kw in data["keywords"]:
            if kw in user_message_lower:
                matched_keyword = kw
                matched_answer = data["answer"]
                break
        if matched_answer:
            break
    
    if not matched_answer:
        # 2. Fuzzy matching
        words = user_message_lower.split()
        all_keywords = []
        mapping = {}
        
        for topic, data in faq.items():
            for kw in data["keywords"]:
                all_keywords.append(kw)
                mapping[kw] = data["answer"]
        
        for w in words:
            close = difflib.get_close_matches(w, all_keywords, n=1, cutoff=0.78)
            if close:
                matched_keyword = close[0]
                matched_answer = mapping[close[0]]
                break
    
    if not matched_answer:
        return None, None
    
    # Decidir o idioma
    # Se a keyword é ambígua, analisar a frase completa
    if matched_keyword in AMBIGUOUS_KEYWORDS:
        detected_lang = detect_language_from_sentence(user_message)
    else:
        # Keyword não-ambígua, inferir da keyword
        detected_lang = infer_lang_from_keyword(matched_keyword) or "pt"
    
    return matched_answer, detected_lang

# -----------------------------------------
# Endpoints
# -----------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").strip()
    user_message_lower = user_message.lower()
    
    # Encontrar match e detectar idioma
    answer_pt, detected_lang = find_best_faq_match(user_message, user_message_lower)
    
    if answer_pt:
        # Traduzir resposta para o idioma detectado
        translated_answer = translate_text(answer_pt, "pt", detected_lang)
        return jsonify({"response": translated_answer})
    
    # Sem match → enviar para Google Sheets
    try:
        requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message}, timeout=3)
    except:
        pass
    
    # Fallback
    fallback_lang = detect_language_from_sentence(user_message)
    fallback = "Pode repetir a sua questão? 😊"
    translated_fallback = translate_text(fallback, "pt", fallback_lang)
    return jsonify({"response": translated_fallback})

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
