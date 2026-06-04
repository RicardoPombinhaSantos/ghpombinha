from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GOOGLE_SHEETS_URL = "https://script.google.com/macros/s/AKfycbxb_0oe7Q8L8_Un01bZoTIiJIw0ndYIgo9j-9mx7VjbZFyZKXW8GxoPj9fGI-6QnCslOw/exec"

# Coordenadas da Praia do Norte / Nazaré
NAZARE_LAT = 39.6045
NAZARE_LON = -9.0642

# -----------------------------------------
# TEMPO — Open-Meteo (grátis, sem chave)
# -----------------------------------------
def get_weather_nazare():
    """Busca previsão do tempo para os próximos 3 dias em Nazaré"""
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

        # WMO weather codes → descrição legível
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
# ONDAS — Open-Meteo Marine API (grátis, sem chave)
# -----------------------------------------
def get_waves_nazare():
    """Busca previsão de ondas para os próximos 3 dias na Praia do Norte"""
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

            # Classificação para surf
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
# DETEÇÃO: pergunta sobre tempo ou ondas?
# -----------------------------------------
def detect_weather_or_waves(message):
    msg = message.lower()

    weather_keywords = [
        "tempo", "weather", "temperatura", "chuva", "sol", "previsão",
        "meteo", "météo", "clima", "forecast", "rain", "sunny", "cloudy",
        "calor", "frio", "hot", "cold", "nublado", "vento", "wind",
        "wetter", "météo", "tiempo", "meteo", "lluvia"
    ]
    wave_keywords = [
        "onda", "ondas", "wave", "waves", "surf", "swell", "praia do norte",
        "altura", "big wave", "surfing", "mar", "sea", "ocean", "welle", "vague"
    ]

    has_weather = any(k in msg for k in weather_keywords)
    has_waves = any(k in msg for k in wave_keywords)

    return has_weather, has_waves


# -----------------------------------------
# FORMATAR DADOS PARA O GROQ
# -----------------------------------------
def format_weather_context(weather, waves):
    context = ""

    if weather:
        context += "\n\nPREVISÃO DO TEMPO EM NAZARÉ (próximos 3 dias):\n"
        for d in weather:
            context += (
                f"- {d['date']}: {d['desc']}, "
                f"máx {d['max']}°C / mín {d['min']}°C, "
                f"chuva {d['rain']}mm\n"
            )

    if waves:
        context += "\nPREVISÃO DE ONDAS — PRAIA DO NORTE (próximos 3 dias):\n"
        for d in waves:
            context += (
                f"- {d['date']}: altura máx {d['height']}m, "
                f"período {d['period']}s — {d['level']}\n"
            )

    return context


# -----------------------------------------
# GROQ AI
# -----------------------------------------
def ask_groq_ai(question, user_lang=None, extra_context=""):
    if not GROQ_API_KEY:
        return None

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
- Shared kitchen available for guests (no breakfast served)
- Payment: cash at check-in (Booking.com accepts card)
- No rental bicycles or vehicles

ATTRACTIONS:
- Praia do Norte (big waves): 5 min by car
- Beaches: Nazaré, S.Martinho do Porto, Paredes da Vitória
- Fátima, Batalha, Alcobaça, Óbidos, Leiria, Ourém, Tomar
- Transport: bus, taxi, Uber
- Fish restaurants: O Veleiro, O Pescador
- Meat restaurant: Tabernassa
- Seafood restaurant: Aki d'el Mar

IMPORTANT:
- If asked about available rooms, direct them to Booking.com or contact: +351 91 055 86 86 / guesthousepombinha@gmail.com
- Answer clearly, politely and concisely
- Do NOT ask questions at the end of the answer
- If weather/wave data is provided below, use it to give an accurate, friendly answer
{extra_context}
"""

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
                "max_tokens": 500
            },
            timeout=10
        )

        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"].strip()
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

    # 1 — Guardar no Google Sheets
    try:
        requests.post(GOOGLE_SHEETS_URL, json={"pergunta": user_message}, timeout=3)
    except:
        pass

    # 2 — Detetar se pergunta sobre tempo ou ondas
    wants_weather, wants_waves = detect_weather_or_waves(user_message)

    weather_data = get_weather_nazare() if wants_weather else None
    wave_data = get_waves_nazare() if wants_waves else None

    # 3 — Formatar contexto extra para o Groq
    extra_context = format_weather_context(weather_data, wave_data)

    # 4 — Responder com Groq AI
    ai_response = ask_groq_ai(user_message, extra_context=extra_context)

    if ai_response:
        return jsonify({
            "response": ai_response,
            "source": "ai",
            "lang": "auto"
        })

    # 5 — Fallback
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
