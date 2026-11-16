"""Evaluacion de desempeno: 20 preguntas del dominio contra ambos chatbots.

Uso:
    python evaluar.py                 # Prolog + LLM
    python evaluar.py --solo-prolog   # sin LLM
    python evaluar.py --pausa 6       # segundos entre llamadas al LLM (limites de cuota)
Genera informe/resultados.json y informe/resultados.md.
La correccion se verifica automaticamente con palabras clave (sin tildes ni
mayusculas) y conviene revisarla a mano antes de entregar.
"""
from __future__ import annotations

import argparse
import json
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import bot_llm
import bot_prolog

RAIZ = Path(__file__).parent
SALIDA_JSON = RAIZ / "informe" / "resultados.json"
SALIDA_MD = RAIZ / "informe" / "resultados.md"

NO_SABE = ["no tengo", "no dispongo", "no hay informacion", "no esta registrad", "no figura",
           "no aparece", "no cuento", "no se encuentra"]
FUERA = NO_SABE + ["no pude", "solo puedo"]

# tipo: que capacidad mide la pregunta
PREGUNTAS = [
    {"q": "¿Quién es el padre de Apolo?", "tipo": "Hecho directo", "debe": ["zeus"]},
    {"q": "¿Quién es la mamá de Atenea?", "tipo": "Sinónimo (mamá)", "debe": ["metis"]},
    {"q": "¿Quiénes son los hermanos de Zeus?", "tipo": "Regla (hermano)",
     "debe": ["demeter", "hades", "hera", "hestia", "poseidon"], "no_debe": ["apolo"]},
    {"q": "¿Quiénes son los abuelos de Apolo?", "tipo": "Regla (abuelo)",
     "debe": ["cronos", "rea", "ceo", "febe"], "no_debe": ["gaia"]},
    {"q": "¿Quiénes son los tíos de Apolo?", "tipo": "Regla compuesta (tío)",
     "debe": ["demeter", "hades", "hera", "hestia", "poseidon"]},
    {"q": "¿Quiénes son los descendientes de Cronos?", "tipo": "Regla recursiva",
     "debe": ["apolo", "ares", "artemisa", "atenea", "demeter", "dionisio", "hades", "hebe", "hefesto",
              "hera", "heracles", "hermes", "hestia", "persefone", "perseo", "poseidon", "triton", "zeus"]},
    {"q": "¿Quién es el dios del mar?", "tipo": "Búsqueda inversa", "debe": ["poseidon"]},
    {"q": "¿De qué es dios Apolo?", "tipo": "Atributo (dominio)",
     "debe": ["sol", "musica", "profecia", "medicina"]},
    {"q": "¿Cuáles son los símbolos de Atenea?", "tipo": "Atributo (símbolo)",
     "debe": ["lechuza", "olivo", "egida"]},
    {"q": "¿Quién es Júpiter?", "tipo": "Alias romano", "debe": ["zeus"]},
    {"q": "¿Dónde vive Hades?", "tipo": "Atributo (residencia)", "debe": ["inframundo"]},
    {"q": "¿Es Zeus hijo de Cronos?", "tipo": "Sí/No (verdadero)", "empieza": "si"},
    {"q": "¿Es Apolo hijo de Poseidón?", "tipo": "Sí/No (falso)", "empieza": "no"},
    {"q": "¿Quién mató a Medusa?", "tipo": "Relación inversa", "debe": ["perseo"]},
    {"q": "¿Cuántos hijos tiene Zeus?", "tipo": "Conteo", "debe": ["11"]},
    {"q": "¿Quiénes son los hijos de Zeus y Hera?", "tipo": "Dos entidades",
     "debe": ["ares", "hebe", "hefesto"], "no_debe": ["apolo", "atenea"]},
    {"q": "¿Con quién está casado Hefesto?", "tipo": "Paráfrasis", "debe": ["afrodita"]},
    {"q": "¿Quién robó el fuego para dárselo a los humanos?", "tipo": "Paráfrasis sin entidad",
     "debe": ["prometeo"], "no_debe": ["hefesto"]},
    {"q": "¿Quién es el padre de Teseo?", "tipo": "Dato ausente en la base",
     "alguno": NO_SABE, "no_debe": ["egeo", "poseidon"]},
    {"q": "¿Cuál es la capital de Francia?", "tipo": "Fuera de dominio",
     "alguno": FUERA, "no_debe": ["paris"]},
]


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in sin_tildes if not unicodedata.combining(c))


def es_correcta(p: dict, respuesta: str) -> bool:
    r = normalizar(respuesta)
    if "empieza" in p and not r.lstrip("¡¿ ").startswith(p["empieza"]):
        return False
    if any(palabra not in r for palabra in p.get("debe", [])):
        return False
    if any(palabra in r for palabra in p.get("no_debe", [])):
        return False
    if "alguno" in p and not any(palabra in r for palabra in p["alguno"]):
        return False
    return True


def ejecutar(funcion, pregunta: str) -> dict:
    inicio = time.perf_counter()
    try:
        respuesta, error = funcion(pregunta), None
    except Exception as e:
        respuesta, error = "", str(e)
    return {"respuesta": respuesta, "error": error, "segundos": round(time.perf_counter() - inicio, 2)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--solo-prolog", action="store_true")
    parser.add_argument("--pausa", type=float, default=4.0, help="segundos entre llamadas al LLM")
    args = parser.parse_args()

    motores = {"prolog": bot_prolog.preguntar}
    if not args.solo_prolog:
        motores["llm"] = bot_llm.preguntar

    filas = []
    for i, p in enumerate(PREGUNTAS, 1):
        fila = {"n": i, "pregunta": p["q"], "tipo": p["tipo"]}
        for nombre, funcion in motores.items():
            res = ejecutar(funcion, p["q"])
            res["correcta"] = None if res["error"] else es_correcta(p, res["respuesta"])
            fila[nombre] = res
            if nombre == "llm" and i < len(PREGUNTAS):
                time.sleep(args.pausa)
        filas.append(fila)
        marcas = "  ".join(f"{m}: {'✓' if fila[m]['correcta'] else ('ERROR' if fila[m]['error'] else '✗')}"
                           for m in motores)
        print(f"{i:2d}. {p['q']:<52} {marcas}")

    resumen = {}
    for m in motores:
        evaluadas = [f[m] for f in filas if f[m]["correcta"] is not None]
        resumen[m] = {
            "correctas": sum(r["correcta"] for r in evaluadas),
            "evaluadas": len(evaluadas),
            "errores": sum(1 for f in filas if f[m]["error"]),
            "tiempo_promedio": round(sum(f[m]["segundos"] for f in filas) / len(filas), 2),
        }
    datos = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "modelo_llm": bot_llm.descripcion_modelo() if "llm" in motores else None,
        "resumen": resumen,
        "filas": filas,
    }
    SALIDA_JSON.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [f"# Resultados de la evaluación ({datos['fecha']})", ""]
    if datos["modelo_llm"]:
        md.append(f"Modelo LLM: {datos['modelo_llm']}\n")
    for m, r in resumen.items():
        md.append(f"- **{m}**: {r['correctas']}/{r['evaluadas']} correctas, {r['errores']} errores, "
                  f"{r['tiempo_promedio']} s promedio")
    md += ["", "| # | Pregunta | Tipo | " + " | ".join(motores) + " |",
           "|---|---|---|" + "---|" * len(motores)]
    for f in filas:
        celdas = []
        for m in motores:
            r = f[m]
            marca = "✓" if r["correcta"] else ("⚠" if r["error"] else "✗")
            celdas.append(f"{marca} {(r['respuesta'] or r['error']).replace('|', '/')}")
        md.append(f"| {f['n']} | {f['pregunta']} | {f['tipo']} | " + " | ".join(celdas) + " |")
    SALIDA_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    print()
    for m, r in resumen.items():
        print(f"{m}: {r['correctas']}/{r['evaluadas']} correctas · {r['tiempo_promedio']} s promedio")
    print(f"Guardado en {SALIDA_JSON.relative_to(RAIZ)} y {SALIDA_MD.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
