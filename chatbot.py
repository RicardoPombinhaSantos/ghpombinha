from flask import Flask, request, jsonify
from flask_cors import CORS
CORS(app)

app = Flask(__name__)

# Respostas simples pré-definidas
faq = {
    "preço": "Os quartos começam a partir de 60€ por noite.",
    "localização": "Estamos em Leiria, a 10 minutos do centro.",
    "check-in": "O check-in é das 14h às 20h.",
    "check-out": "O check-out é até às 11h."
}

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "").lower()
    for key, answer in faq.items():
        if key in user_message:
            return jsonify({"response": answer})
    return jsonify({"response": "Pode repetir a sua questão? 😊"})

if __name__ == "__main__":
    app.run(debug=True)

