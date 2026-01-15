from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# -----------------------------------------
# CONFIGURAÇÃO GROQ API (GRATUITA)
# -----------------------------------------
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbxb_0oe7Q8L8_Un01bZoTIiJIw0ndYIgo9j-9mx7VjbZFyZKXW8GxoPj9fGI-6QnCslOw/exec"

# -----------------------------------------
# DETECÇÃO DE IDIOMA
# -----------------------------------------
def detect_language(text):
    """Detecta o idioma da mensagem"""
    if not text or not text.strip():
        return "pt"
    
    lower = text.lower()
    
    pt_indicators = ["é", "são", "que", "qual", "onde", "quando", "quanto", "a que horas", "às", "das", "preço"]
    en_indicators = ["is", "are", "what", "when", "where", "how", "at what time", "the", "price"]
    es_indicators = ["es", "son", "qué", "cuál", "dónde", "cuándo", "a qué hora", "las", "precio"]
    fr_indicators = ["est", "sont", "quel", "quelle", "où", "quand", "à quelle heure", "les", "prix"]
    de_indicators = ["ist", "sind", "was", "wo", "wann", "um wie viel uhr", "die", "preis"]
    it_indicators = ["è", "sono", "che", "quale", "dove", "quando", "prezzo"]
    
    scores = {
        "pt": sum(1 for w in pt_indicators if w in lower),
        "en": sum(1 for w in en_indicators if w in lower),
        "es": sum(1 for w in es_indicators if w in lower),
        "fr": sum(1 for w in fr_indicators if w in lower),
        "de": sum(1 for w in de_indicators if w in lower),
        "it": sum(1 for w in it_indicators if w in lower)
    }
    
    max_lang = max(scores, key=scores.get)
    return max_lang if scores[max_lang] > 0 else "pt"

# -----------------------------------------
# GROQ AI COM PROMPTS MULTILINGUES
# -----------------------------------------
def ask_groq_ai(question, user_lang="pt"):
    """Usa Groq AI para responder perguntas"""
    if not GROQ_API_KEY:
        return None
    
    # System prompts por idioma
    system_prompts = {
        "pt": """Você é um assistente de um alojamento na Nazaré, Portugal. 

INFORMAÇÕES:
Localização: Nazaré, 5min centro (carro), 30min (pé)
Quartos: 60€+/noite (duplos, twin, familiares)
Check-in: 15h-21h | Check-out: 11:30h
Wi-Fi e estacionamento gratuitos
Aceitamos animais (pedido prévio)
Pequeno-almoço: algumas tarifas
Pagamento: cartão ou dinheiro

ATRAÇÕES:
Praia do Norte (ondas): 5min carro
Praias: São Pedro Moel, Vieira, Nazaré
Fátima, Batalha, Alcobaça, Castelo
Transporte: Leiria (autocarro/comboio) → táxi
Restaurantes: O Casarão, Taberna do Terreiro, Mata Bicho

IMPORTANTE: Responda SEMPRE em PORTUGUÊS, mesmo que a pergunta seja noutro idioma.""",
        
        "en": """You are an assistant for accommodation in Nazaré, Portugal.

INFO:
Location: Nazaré, 5min center (car), 30min (walk)
Rooms: €60+/night (doubles, twins, family)
Check-in: 3PM-9PM | Check-out: 11:30AM
Free Wi-Fi and parking
Pets accepted (prior request)
Breakfast: some rates
Payment: card or cash

ATTRACTIONS:
Praia do Norte (waves): 5min car
Beaches: São Pedro Moel, Vieira, Nazaré
Fátima, Batalha, Alcobaça, Castle
Transport: Leiria (bus/train) → taxi
Restaurants: O Casarão, Taberna do Terreiro, Mata Bicho

CRITICAL: Answer ONLY in ENGLISH, regardless of question language. Never answer in Portuguese.""",
        
        "es": """Eres asistente de alojamiento en Nazaré, Portugal.

INFO:
Ubicación: Nazaré, 5min centro (coche), 30min (pie)
Habitaciones: 60€+/noche (dobles, twin, familiares)
Check-in: 15h-21h | Check-out: 11:30h
Wi-Fi y parking gratis
Aceptamos mascotas (petición previa)
Desayuno: algunas tarifas
Pago: tarjeta o efectivo

ATRACCIONES:
Praia do Norte (olas): 5min coche
Playas: São Pedro Moel, Vieira, Nazaré
Fátima, Batalha, Alcobaça, Castillo
Transporte: Leiria (bus/tren) → taxi
Restaurantes: O Casarão, Taberna do Terreiro, Mata Bicho

CRÍTICO: Responde SOLO en ESPAÑOL, sin importar el idioma de la pregunta. Nunca en portugués.""",
        
        "fr": """Vous êtes assistant d'hébergement à Nazaré, Portugal.

INFO:
Emplacement: Nazaré, 5min centre (voiture), 30min (pied)
Chambres: 60€+/nuit (doubles, twin, familiales)
Enregistrement: 15h-21h | Départ: 11h30
Wi-Fi et parking gratuits
Animaux acceptés (demande préalable)
Petit-déjeuner: certains tarifs
Paiement: carte ou espèces

ATTRACTIONS:
Praia do Norte (vagues): 5min voiture
Plages: São Pedro Moel, Vieira, Nazaré
Fátima, Batalha, Alcobaça, Château
Transport: Leiria (bus/train) → taxi
Restaurants: O Casarão, Taberna do Terreiro, Mata Bicho

CRITIQUE: Répondez UNIQUEMENT en FRANÇAIS, quelle que soit la langue de la question. Jamais en portugais.""",
        
        "it": """Sei assistente di alloggio a Nazaré, Portogallo.

INFO:
Posizione: Nazaré, 5min centro (auto), 30min (piedi)
Camere: 60€+/notte (doppie, twin, familiari)
Check-in: 15-21 | Check-out: 11:30
Wi-Fi e parcheggio gratuiti
Accettiamo animali (richiesta preventiva)
Colazione: alcune tariffe
Pagamento: carta o contanti

ATTRAZIONI:
Praia do Norte (onde): 5min auto
Spiagge: São Pedro Moel, Vieira, Nazaré
Fátima, Batalha, Alcobaça, Castello
Trasporto: Leiria (bus/treno) → taxi
Ristoranti: O Casarão, Taberna do Terreiro, Mata Bicho

CRITICO: Rispondi SOLO in ITALIANO, indipendentemente dalla lingua della domanda. Mai in portoghese.""",
        
        "de": """Sie sind Assistent für Unterkunft in Nazaré, Portugal.

INFO:
Standort: Nazaré, 5min Zentrum (Auto), 30min (Fuß)
Zimmer: 60€+/Nacht (Doppel, Twin, Familien)
Check-in: 15-21 Uhr | Check-out: 11:30 Uhr
Kostenloses WLAN und Parkplatz
Haustiere erlaubt (vorherige Anfrage)
Frühstück: einige Tarife
Zahlung: Karte oder Bargeld

SEHENSWÜRDIGKEITEN:
Praia do Norte (Wellen): 5min Auto
Strände: São Pedro Moel, Vieira, Nazaré
Fátima, Batalha, Alcobaça, Burg
Transport: Leiria (Bus/Zug) → Taxi
Restaurants: O Casarão, Taberna do Terreiro, Mata Bicho

KRITISCH: Antworten Sie NUR auf DEUTSCH, unabhängig von der Fragesprache. Niemals auf Portugiesisch."""
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
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                "temperature": 0.7,
                "max_tokens": 400
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
# ENDPOINTS
# -----------------------------------------
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message", "").strip()
    user_lang = data.get("lang")
    
    # Se não vier idioma do frontend, detectar
    if not user_lang:
        user_lang = detect_language(user_message)
    
    # Tentar responder com Groq AI
    ai_response = ask_groq_ai(user_message, user_lang)
    
    if ai_response:
        return jsonify({
            "response": ai_response, 
            "source": "ai",
            "lang": user_lang
        })
    
    # Se AI falhar, registar no Sheets e dar fallback
    try:
        requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message}, timeout=3)
    except:
        pass
    
    # Fallback por idioma
    fallbacks = {
        "pt": "Desculpe, estou com dificuldades técnicas. Pode contactar-nos diretamente? 😊",
        "en": "Sorry, I'm having technical difficulties. Could you contact us directly? 😊",
        "es": "Disculpe, tengo dificultades técnicas. ¿Puede contactarnos directamente? 😊",
        "fr": "Désolé, j'ai des difficultés techniques. Pouvez-vous nous contacter directement? 😊",
        "it": "Scusa, ho difficoltà tecniche. Puoi contattarci direttamente? 😊",
        "de": "Entschuldigung, ich habe technische Schwierigkeiten. Können Sie uns direkt kontaktieren? 😊"
    }
    
    fallback = fallbacks.get(user_lang, fallbacks["pt"])
    return jsonify({
        "response": fallback, 
        "source": "fallback",
        "lang": user_lang
    })

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
