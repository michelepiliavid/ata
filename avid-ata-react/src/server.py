from flask import Flask, jsonify, request
from flask_cors import CORS  # Importa CORS
import random

app = Flask(__name__)

# Abilita CORS su tutte le rotte
CORS(app)

@app.route('/rest/conversation/get_simple_answer')
def get_simple_answer():
    prompt = request.args.get('prompt', '')
    answers = [
        "La risposta alla tua domanda è che dipende.",
        "Non sono sicuro, ma potrei chiedere.",
        "Probabilmente la risposta è più semplice di quanto pensi.",
        "Dovresti dare un'occhiata ai dettagli.",
        "Per favore, forniscimi più informazioni.",
        "Hmm, interessante domanda!",
        "Devi approfondire un po' di più su questo.",
        "La soluzione potrebbe essere più chiara di quanto sembri.",
        "Penso che la risposta sia abbastanza ovvia.",
        "Forse dovremmo fare una ricerca insieme."
    ]
    
    # Rispondi con una risposta casuale
    answer = random.choice(answers)

    # Restituisci come JSON
    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
