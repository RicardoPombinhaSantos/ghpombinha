from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import difflib
import os

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# CONFIGURAÇÃO GROQ API (GRATUITA)
# -----------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")  # Adicionar no Render
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

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
# Keywords ambíguas
# -----------------------------------------
AMBIGUOUS_KEYWORDS = {"check-in", "check in", "check-out", "check out", "wifi", "wi-fi", "internet"}

# -----------------------------------------
# Inferir idioma
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

def detect_language_from_sentence(text):
    if not text or not text.strip():
        return "pt"
    
    lower = text.lower()
    pt_indicators = ["é", "são", "que", "qual", "onde", "quando", "quanto", "a que horas", "às", "das"]
    en_indicators = ["is", "are", "what", "when", "where", "how", "at what time", "the"]
    es_indicators = ["es", "son", "qué", "cuál", "dónde", "cuándo", "a qué hora", "las"]
    fr_indicators = ["est", "sont", "quel", "quelle", "où", "quand", "à quelle heure", "les"]
    de_indicators = ["ist", "sind", "was", "wo", "wann", "um wie viel uhr", "die"]
    
    scores = {
        "pt": sum(1 for w in pt_indicators if w in lower),
        "en": sum(1 for w in en_indicators if w in lower),
        "es": sum(1 for w in es_indicators if w in lower),
        "fr": sum(1 for w in fr_indicators if w in lower),
        "de": sum(1 for w in de_indicators if w in lower)
    }
    
    max_lang = max(scores, key=scores.get)
    return max_lang if scores[max_lang] > 0 else "pt"

def translate_text(text, source_lang, target_lang):
    if not text or source_lang == target_lang:
        return text
    
    manual = MANUAL_ANSWER_TRANSLATIONS.get(text.strip())
    if manual:
        code = target_lang.lower()[:2]
        return manual.get(code, text)
    
    return text

def find_best_faq_match(user_message, user_message_lower):
    matched_keyword = None
    matched_answer = None
    
    for topic, data in faq.items():
        for kw in data["keywords"]:
            if kw in user_message_lower:
                matched_keyword = kw
                matched_answer = data["answer"]
                break
        if matched_answer:
            break
    
    if not matched_answer:
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
    
    if matched_keyword in AMBIGUOUS_KEYWORDS:
        detected_lang = detect_language_from_sentence(user_message)
    else:
        detected_lang = infer_lang_from_keyword(matched_keyword) or "pt"
    
    return matched_answer, detected_lang

# -----------------------------------------
# INTEGRAÇÃO GROQ AI (GRATUITA)
# -----------------------------------------
def ask_groq_ai(question, user_lang="pt"):
    """Usa Groq AI para responder perguntas fora do FAQ"""
    if not GROQ_API_KEY:
        return None
    
    # System prompt multilingue sobre o alojamento
    system_prompts = {
        "pt": """Você é um assistente de um alojamento na Nazaré, Portugal. 
Informações sobre o alojamento:
- Localização: Nazaré, a 5 minutos do centro de carro, 30 minutos a pé
- Quartos a partir de 60€/noite
- Check-in: 15h-21h | Check-out: até 11:30h
- Wi-Fi gratuito e estacionamento gratuito
- Aceitamos animais (pedido prévio)
- Perto das ondas gigantes da Praia do Norte (5 min de carro)
- Atrações próximas: Santuário de Fátima, Mosteiro da Batalha, Alcobaça, São Pedro de Moel
- Restaurantes recomendados: O Casarão, Taberna do Terreiro, Mata Bicho

Responda de forma amigável, breve e útil. Se não souber algo específico, seja honesto.""",
        
        "en": """You are an assistant for an accommodation in Nazaré, Portugal.
Accommodation information:
- Location: Nazaré, 5 minutes from center by car, 30 minutes on foot
- Rooms from €60/night
- Check-in: 3PM-9PM | Check-out: until 11:30AM
- Free Wi-Fi and free parking
- We accept pets (prior request)
- Near the giant waves of Praia do Norte (5 min by car)
- Nearby attractions: Fátima Sanctuary, Batalha Monastery, Alcobaça, São Pedro de Moel
- Recommended restaurants: O Casarão, Taberna do Terreiro, Mata Bicho

Answer in a friendly, brief and helpful way. If you don't know something specific, be honest.""",
        
        "es": """Eres un asistente de un alojamiento en Nazaré, Portugal.
Información del alojamiento:
- Ubicación: Nazaré, a 5 minutos del centro en coche, 30 minutos a pie
- Habitaciones desde 60€/noche
- Check-in: 15h-21h | Check-out: hasta 11:30h
- Wi-Fi gratis y aparcamiento gratuito
- Aceptamos mascotas (petición previa)
- Cerca de las olas gigantes de Praia do Norte (5 min en coche)
- Atracciones cercanas: Santuario de Fátima, Monasterio de Batalha, Alcobaça, São Pedro de Moel
- Restaurantes recomendados: O Casarão, Taberna do Terreiro, Mata Bicho

Responde de forma amigable, breve y útil. Si no sabes algo específico, sé honesto.""",
        
        "fr": """Vous êtes un assistant d'un hébergement à Nazaré, Portugal.
Informations sur l'hébergement:
- Emplacement: Nazaré, à 5 minutes du centre en voiture, 30 minutes à pied
- Chambres à partir de 60€/nuit
- Enregistrement: 15h-21h | Départ: jusqu'à 11h30
- Wi-Fi gratuit et parking gratuit
- Nous acceptons les animaux (demande préalable)
- Près des vagues géantes de Praia do Norte (5 min en voiture)
- Attractions à proximité: Sanctuaire de Fátima, Monastère de Batalha, Alcobaça, São Pedro de Moel
- Restaurants recommandés: O Casarão, Taberna do Terreiro, Mata Bicho

Répondez de manière amicale, brève et utile. Si vous ne savez pas quelque chose de spécifique, soyez honnête.""",
        
        "it": """Sei un assistente di un alloggio a Nazaré, Portogallo.
Informazioni sull'alloggio:
- Posizione: Nazaré, a 5 minuti dal centro in auto, 30 minuti a piedi
- Camere da 60€/notte
- Check-in: 15-21 | Check-out: fino alle 11:30
- Wi-Fi gratuito e parcheggio gratuito
- Accettiamo animali (richiesta preventiva)
- Vicino alle onde giganti di Praia do Norte (5 min in auto)
- Attrazioni vicine: Santuario di Fátima, Monastero di Batalha, Alcobaça, São Pedro de Moel
- Ristoranti consigliati: O Casarão, Taberna do Terreiro, Mata Bicho

Rispondi in modo amichevole, breve e utile. Se non sai qualcosa di specifico, sii onesto.""",
        
        "de": """Sie sind ein Assistent für eine Unterkunft in Nazaré, Portugal.
Informationen zur Unterkunft:
- Standort: Nazaré, 5 Minuten vom Zentrum mit dem Auto, 30 Minuten zu Fuß
- Zimmer ab 60€/Nacht
- Check-in: 15-21 Uhr | Check-out: bis 11:30 Uhr
- Kostenloses WLAN und kostenlose Parkplätze
- Wir akzeptieren Haustiere (vorherige Anfrage)
- In der Nähe der riesigen Wellen von Praia do Norte (5 Min. mit dem Auto)
- Sehenswürdigkeiten in der Nähe: Heiligtum von Fátima, Kloster Batalha, Alcobaça, São Pedro de Moel
- Empfohlene Restaurants: O Casarão, Taberna do Terreiro, Mata Bicho

Antworten Sie freundlich, kurz und hilfreich. Wenn Sie etwas Bestimmtes nicht wissen, seien Sie ehrlich."""
    }
    
    system_prompt = system_prompts.get(user_lang, system_prompts["pt"])
    
    try:
        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",  # Modelo grátis e rápido
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Groq API Exception: {e}")
        return None

# -----------------------------------------
# Endpoints
# -----------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    user_lang = data.get("lang", "pt")
    user_message_lower = user_message.lower()
    
    # 1. Tentar FAQ primeiro
    answer_pt, detected_lang = find_best_faq_match(user_message, user_message_lower)
    target_lang = user_lang if user_lang else (detected_lang or "pt")
    
    if answer_pt:
        translated_answer = translate_text(answer_pt, "pt", target_lang)
        return jsonify({"response": translated_answer, "source": "faq"})
    
    # 2. Se não encontrou no FAQ, tentar Groq AI
    ai_response = ask_groq_ai(user_message, target_lang)
    
    if ai_response:
        return jsonify({"response": ai_response, "source": "ai"})
    
    # 3. Se AI não disponível, registar no Sheets
    try:
        requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message}, timeout=3)
    except:
        pass
    
    # 4. Fallback final
    fallback = "Pode repetir a sua questão? 😊"
    translated_fallback = translate_text(fallback, "pt", target_lang)
    return jsonify({"response": translated_fallback, "source": "fallback"})

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
