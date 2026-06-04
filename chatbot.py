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

# Coordenadas da Praia do Norte / Nazaré
NAZARE_LAT = 39.6045
NAZARE_LON = -9.0642

# -----------------------------------------
# TEMPO (Open-Meteo, grátis, sem chave)
# -----------------------------------------
def get_weather_nazare():
    try:
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={NAZARE_LAT}&longitude={NAZARE_LON}"
            f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode"
            f"&timezone=Europe%2FLisbon&forecast_days=3"
        )
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None

        d = r.json()["daily"]

        def wmo_desc(code):
            if code == 0: return "céu limpo ☀️"
            elif code in [1, 2]: return "parcialmente nublado 🌤️"
            elif code == 3: return "nublado ☁️"
            elif code in [45, 48]: return "nevoeiro 🌫️"
            elif code in [51, 53, 55, 61, 63, 65]: return "chuva 🌧️"
            elif code in [71, 73, 75]: return "neve 🌨️"
            elif code in [80, 81, 82]: return "aguaceiros 🌦️"
            elif code in [95, 96, 99]: return "trovoada ⛈️"
            else: return "variável"

        days = []
        for i in range(3):
            days.append({
                "date": d["time"][i],
                "max": d["temperature_2m_max"][i],
                "min": d["temperature_2m_min"][i],
                "rain": d["precipitation_sum"][i],
                "desc": wmo_desc(d["weathercode"][i])
            })
        return days

    except Exception as e:
        print(f"Weather error: {e}")
        return None


# -----------------------------------------
# ONDAS (Open-Meteo Marine, grátis, sem chave)
# -----------------------------------------
def get_waves_nazare():
    try:
        url = (
            f"https://marine-api.open-meteo.com/v1/marine"
            f"?latitude={NAZARE_LAT}&longitude={NAZARE_LON}"
            f"&daily=wave_height_max,wave_period_max,wind_wave_height_max"
            f"&timezone=Europe%2FLisbon&forecast_days=3"
        )
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None

        d = r.json()["daily"]

        days = []
        for i in range(3):
            height = d["wave_height_max"][i]
            period = d["wave_period_max"][i]

            if height < 1.0:
                surf_level = "pequenas 🏊"
            elif height < 2.5:
                surf_level = "médias — boas para surf 🏄"
            elif height < 5.0:
                surf_level = "grandes — surf avançado 🌊"
            else:
                surf_level = "muito grandes — perigosas, apenas para big wave 🌊🔥"

            days.append({
                "date": d["time"][i],
                "height": height,
                "period": period,
                "level": surf_level
            })
        return days

    except Exception as e:
        print(f"Waves error: {e}")
        return None


# -----------------------------------------
# Detetar se pergunta sobre tempo ou ondas
# -----------------------------------------
def detect_weather_or_waves(message):
    msg = message.lower()

    weather_keywords = [
        "tempo", "weather", "temperatura", "chuva", "sol", "previsão",
        "meteo", "météo", "clima", "forecast", "rain", "sunny", "cloudy",
        "calor", "frio", "hot", "cold", "nublado", "vento", "wind",
        "wetter", "tiempo", "lluvia"
    ]
    wave_keywords = [
        "onda", "ondas", "wave", "waves", "surf", "swell", "praia do norte",
        "altura", "big wave", "surfing", "mar", "sea", "ocean", "welle", "vague"
    ]

    has_weather = any(k in msg for k in weather_keywords)
    has_waves = any(k in msg for k in wave_keywords)

    return has_weather, has_waves


# -----------------------------------------
# Formatar contexto de tempo/ondas para o Groq
# -----------------------------------------
METEOBLUE_URL = "https://www.meteoblue.com/pt/tempo/semana/nazar%C3%A9_portugal_2266931"

WEATHER_FALLBACK = {
    "pt": f"NOTA INTERNA: Foi pedida informação sobre o tempo mas a API meteorológica não respondeu. Informa o utilizador que não foi possível obter os dados neste momento e sugere que consulte {METEOBLUE_URL}",
    "en": f"INTERNAL NOTE: Weather was requested but the weather API did not respond. Tell the user you couldn't get the data right now and suggest they check {METEOBLUE_URL}",
    "es": f"NOTA INTERNA: Se solicitó información del tiempo pero la API no respondió. Informa al usuario que no fue posible obtener los datos ahora mismo y sugiere que consulte {METEOBLUE_URL}",
    "fr": f"NOTE INTERNE: La météo a été demandée mais l'API n'a pas répondu. Informe l'utilisateur que les données ne sont pas disponibles pour l'instant et suggère de consulter {METEOBLUE_URL}",
    "it": f"NOTA INTERNA: È stata richiesta la previsione meteo ma l'API non ha risposto. Informa l'utente che i dati non sono disponibili al momento e suggerisci di consultare {METEOBLUE_URL}",
    "de": f"INTERNER HINWEIS: Wetter wurde angefragt, aber die API hat nicht geantwortet. Teile dem Nutzer mit, dass die Daten gerade nicht verfügbar sind, und empfehle {METEOBLUE_URL}",
}

def format_weather_context(weather, waves, user_lang=None):
    context = ""

    if weather:
        context += "\n\nPREVISÃO DO TEMPO EM NAZARÉ (próximos 3 dias):\n"
        for d in weather:
            context += (
                f"- {d['date']}: {d['desc']}, "
                f"máx {d['max']}°C / mín {d['min']}°C, "
                f"chuva {d['rain']}mm\n"
            )
    elif weather is None:
        lang = user_lang or "pt"
        context += f"\n\n{WEATHER_FALLBACK.get(lang, WEATHER_FALLBACK['en'])}\n"

    if waves:
        context += "\nPREVISÃO DE ONDAS — PRAIA DO NORTE (próximos 3 dias):\n"
        for d in waves:
            context += (
                f"- {d['date']}: altura máx {d['height']}m, "
                f"período {d['period']}s — {d['level']}\n"
            )

    return context


# -----------------------------------------
# GROQ AI — DETEÇÃO AUTOMÁTICA DE IDIOMA
# -----------------------------------------
def ask_groq_ai(question, user_lang=None, extra_context=""):
    """Usa Groq AI para responder perguntas com autodetecção de idioma"""

    if not GROQ_API_KEY:
        return None

    if user_lang is None:
        system_prompt = f"""
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
If weather or wave data is provided below, use it to give an accurate and friendly answer.
{extra_context}
"""
    else:
        system_prompts = {
            "pt": f"""Tu és uma assistente de uma GuestHouse na Nazaré, Portugal.
            O teu nome é Pombinha.
IMPORTANTE:
Responde SEMPRE em Português Europeu (PT‑PT). 
Nunca uses expressões, ortografia ou construções do Português do Brasil.
Responde em feminino quando falares sobre a GuestHouse, que está situada na Nazaré.
INFORMAÇÕES:
Localização: Nazaré, 5min centro (carro), 30min (pé)
Quartos: A partir de 35€/noite (dependendo da época)
Check-in: 15h-21h | Check-out: 11:30h
Wi-Fi e estacionamento gratuitos
Não são permitidos animais
Não temos Pequeno-almoço (Dispomos de uma cozinha partilhada apenas para os nossos Hóspedes onde podem confecionar todas as refeições)
Pagamento: dinheiro no acto do check-in (no Booking.com é com cartão)
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
Responde na Nazaré, nunca em Nazaré.
Se perguntarem por quartos vagos, envia-os para booking.com ou contactar-nos directamente através do +351 91 055 86 86 ou pelo email guesthousepombinha@gmail.com.
Não faças perguntas no fim da resposta.
Se tiveres dados de tempo ou ondas abaixo, usa-os para responder com precisão.
{extra_context}""",

            "en": f"""You are an assistant for accommodation in Nazaré, Portugal.
Answer ONLY in ENGLISH.
If weather or wave data is provided below, use it to give an accurate and friendly answer.
{extra_context}""",

            "es": f"""Eres asistente de alojamiento en Nazaré, Portugal.
Responde SOLO en ESPAÑOL.
Si hay datos de tiempo u olas abajo, úsalos para responder con precisión.
{extra_context}""",

            "fr": f"""Vous êtes assistant d'hébergement à Nazaré, Portugal.
Répondez UNIQUEMENT en FRANÇAIS.
Si des données météo ou de vagues sont fournies ci-dessous, utilisez-les pour répondre avec précision.
{extra_context}""",

            "it": f"""Sei assistente di alloggio a Nazaré, Portogallo.
Rispondi SOLO in ITALIANO.
Se sono forniti dati meteo o onde qui sotto, usali per rispondere con precisione.
{extra_context}""",

            "de": f"""Sie sind Assistent für Unterkunft in Nazaré, Portugal.
Antworten Sie NUR auf DEUTSCH.
Wenn unten Wetter- oder Wellendaten vorhanden sind, nutzen Sie diese für eine genaue Antwort.
{extra_context}"""
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

    # 3 — Detetar se pergunta sobre tempo ou ondas e buscar dados
    wants_weather, wants_waves = detect_weather_or_waves(user_message)
    weather_data = get_weather_nazare() if wants_weather else None
    wave_data = get_waves_nazare() if wants_waves else None
    extra_context = format_weather_context(weather_data, wave_data, user_lang)

    # 4 — Tentar responder com Groq AI
    ai_response = ask_groq_ai(user_message, user_lang, extra_context=extra_context)

    if ai_response:
        return jsonify({
            "response": ai_response,
            "source": "ai",
            "lang": "auto"
        })

    # 5 — Fallback genérico
    return jsonify({
        "response": "Desculpe, estou com dificuldades técnicas. Pode contactar-nos diretamente? +351 91 055 86 86 😊",
        "source": "fallback",
        "lang": "pt"
    })


@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
