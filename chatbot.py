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
# GROQ AI — DETEÇÃO AUTOMÁTICA DE IDIOMA
# -----------------------------------------
def ask_groq_ai(question, user_lang=None):
    """Usa Groq AI para responder perguntas com autodetecção de idioma"""

    if not GROQ_API_KEY:
        return None

    # Se não houver idioma, pedir ao Groq para detectar automaticamente
    if user_lang is None:
        system_prompt = """
You are an assistant for a GuestHouse in Nazaré, Portugal.
Your name is Pombinha.
Detect the user's language with maximum accuracy and ALWAYS answer in that language.

ACCOMMODATION INFORMATION:
- Location: Nazaré, 5 min from the center by car, 30 min walking
- Rooms: from 35€/night (depending the season)
- Check‑in: 15:00–21:00
- Check‑out: 11:30
- Free Wi‑Fi and free parking
- Pets not allowed
- Breakfast (We have a shared kitchen only for the Guests)
- Payment: cash (in Booking.com is by card)
- No rental bicicles
- No Rental vehicles

ATTRACTIONS:
- Praia do Norte (big waves): 5 min by car
- Beaches: Nazaré, S.Martinho do Porto, Paredes da Vitória
- Fátima, Batalha, Alcobaça, Óbidos, Leiria, Ourém, Tomar
- Transport: bus, taxi, Uber
- Restaurants for fish: O Veleiro, O Pescador
- Restaurants for meat: Tabernassa
- Restaurants sea food: Aki d'el Mar

IMPORTANT:
If asked about rooms, don't say prices, send them to Booking.com or to contact us directly, to the number +351 91 055 86 86 or by email guesthousepombinha@gmail.com.
Always answer clearly, politely and concisely.
Do not ask questions at the end of the answer.
If the words are most of them in English, answer in English.
"""
    else:
        # System prompts por idioma (mantidos caso precises no futuro)
        system_prompts = {
            "pt": """Tu és uma assistente de uma GuestHouse na Nazaré, Portugal.
            O teu nome é Pombinha.
IMPORTANTE:
Responde SEMPRE em Português Europeu (PT‑PT). 
Nunca uses expressões, ortografia ou construções do Português do Brasil.
Responde em feminino quando falares sobre a GuestHouse.
INFORMAÇÕES:
Localização: Nazaré, 5min centro (carro), 30min (pé)
Quartos: A partir de 35€/noite (dependendo da época)
Check-in: 15h-21h | Check-out: 11:30h
Wi-Fi e estacionamento gratuitos
Não são permitidos animais
Não temos Pequeno-almoço (Dispomos de uma cozinha partilhada apenas para os nossos Hóspedesonde podem confecionar todas as refeições)
Pagamento: dinheiro (no Booking.com é com cartão)
Não temos bicicletas
Não alugamos veiculos

ATRAÇÕES:
Praia do Norte (ondas): 5min carro
Praias: Nazaré, S.Martinho do Porto, Paredes da Vitória
Fátima, Batalha, Alcobaça, Óbidos, Leiria, Ourém, Tomar
Transporte: bus, taxi, Uber
Restaurantes para comer peixe: O Veleiro, O Pescador
Restaurantes para comer carne: Tabernassa
Restaurantes Marisco: Aki d'el Mar

IMPORTANTE: Responda SEMPRE em PORTUGUÊS.
Se perguntarem por quartos vagos, envia-os para booking.com ou contactar-nos directamente através do +351 91 055 86 86 ou pelo email guesthousepombinha@gmail.com.
Não faças perguntas no fim da resposta.""",

            "en": """You are an assistant for accommodation in Nazaré, Portugal.
Answer ONLY in ENGLISH.""",

            "es": """Eres asistente de alojamiento en Nazaré, Portugal.
Responde SOLO en ESPAÑOL.""",

            "fr": """Vous êtes assistant d'hébergement à Nazaré, Portugal.
Répondez UNIQUEMENT en FRANÇAIS.""",

            "it": """Sei assistente di alloggio a Nazaré, Portogallo.
Rispondi SOLO in ITALIANO.""",

            "de": """Sie sind Assistent für Unterkunft in Nazaré, Portugal.
Antworten Sie NUR auf DEUTSCH."""
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

    # 1 — Guardar SEMPRE no Google Sheets
    try:
        requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message}, timeout=3)
    except:
        pass

    # 2 — Forçar autodetecção do Groq
    user_lang = None

    # 3 — Tentar responder com Groq AI
    ai_response = ask_groq_ai(user_message, user_lang)

    if ai_response:
        return jsonify({
            "response": ai_response,
            "source": "ai",
            "lang": "auto"
        })

    # 4 — Fallback genérico
    return jsonify({
        "response": "Desculpe, estou com dificuldades técnicas. Pode contactar-nos diretamente? 😊",
        "source": "fallback",
        "lang": "pt"
    })


@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
