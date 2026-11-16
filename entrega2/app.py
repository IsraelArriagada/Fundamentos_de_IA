"""Interfaz web del chatbot (frontend + API).

Ejecutar:  python app.py   y abrir http://127.0.0.1:5000
API:       POST /api/preguntar  {"pregunta": "...", "motor": "prolog" | "llm" | "ambos"}
"""
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import bot_llm
import bot_prolog

MOTORES = {"prolog": bot_prolog.preguntar, "llm": bot_llm.preguntar}
MAX_LARGO = 300

app = Flask(__name__, static_folder=str(Path(__file__).parent / "web"), static_url_path="")


def consultar(motor: str, pregunta: str) -> dict:
    inicio = time.perf_counter()
    try:
        respuesta, ok = MOTORES[motor](pregunta), True
    except Exception as e:  # el error se muestra al usuario, la app no se cae
        respuesta, ok = f"Error: {e}", False
    return {"motor": motor, "respuesta": respuesta, "ok": ok,
            "segundos": round(time.perf_counter() - inicio, 2)}


@app.get("/")
def inicio():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/api/estado")
def estado():
    return jsonify({"llm": bot_llm.descripcion_modelo()})


@app.post("/api/preguntar")
def preguntar():
    datos = request.get_json(silent=True) or {}
    pregunta = str(datos.get("pregunta", "")).strip()
    motor = datos.get("motor", "prolog")
    if not pregunta:
        return jsonify({"error": "La pregunta está vacía."}), 400
    if len(pregunta) > MAX_LARGO:
        return jsonify({"error": f"La pregunta supera {MAX_LARGO} caracteres."}), 400
    motores = list(MOTORES) if motor == "ambos" else [motor]
    if any(m not in MOTORES for m in motores):
        return jsonify({"error": "Motor inválido. Usa prolog, llm o ambos."}), 400
    with ThreadPoolExecutor(max_workers=len(motores)) as ex:
        resultados = list(ex.map(lambda m: consultar(m, pregunta), motores))
    return jsonify({"pregunta": pregunta, "resultados": resultados})


if __name__ == "__main__":
    app.run(debug=False, port=5000)
