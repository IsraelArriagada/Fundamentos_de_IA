"""Chatbot v2: LLM restringido a la base de conocimiento de prolog/kb.pl.

El conocimiento NO se duplica: en cada pregunta se exportan los hechos de
kb.pl (prolog/exportar.pl) y se entregan al LLM como contexto, junto con las
reglas en lenguaje natural. Si se edita kb.pl, el LLM ve el cambio de inmediato.

Configuracion por variables de entorno (o archivo .env, ver .env.example):
    LLM_PROVIDER = openai | gemini | groq | ollama | anthropic
    LLM_MODEL    = nombre del modelo (opcional, hay valores por defecto)
    <PROVEEDOR>_API_KEY o LLM_API_KEY
Solo usa la biblioteca estandar de Python.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).parent
KB = RAIZ / "prolog" / "kb.pl"
EXPORTADOR = RAIZ / "prolog" / "exportar.pl"

# proveedor -> (url base, variable con la clave, modelo por defecto)
PROVEEDORES = {
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY", "gemini-2.5-flash"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "ollama": ("http://localhost:11434/v1", None, "llama3.1"),
    "anthropic": ("https://api.anthropic.com/v1", "ANTHROPIC_API_KEY", "claude-haiku-4-5"),
}

SIN_INFO = "No tengo esa información en mi base de conocimiento."

INSTRUCCIONES = f"""Eres un chatbot experto en mitología griega. Respondes en español, en una o dos oraciones.

REGLAS ESTRICTAS:
1. Usa ÚNICAMENTE los hechos de la BASE DE CONOCIMIENTO de abajo. No uses tu conocimiento general,
   aunque lo sepas. Si la respuesta no se puede obtener de esos hechos, responde exactamente:
   "{SIN_INFO}"
2. Si la pregunta no trata de mitología griega, responde: "Solo puedo responder preguntas sobre mitología griega."
3. En preguntas de sí/no, comienza con "Sí" o "No".
4. Cuando enumeres personajes, nómbralos a todos, sin omitir ninguno ni agregar otros.
5. Puedes deducir relaciones aplicando SOLO estas reglas (lógica de primer orden):
   - padre(P,H): P es progenitor de H y P es de género masculino. madre: análogo con género femenino.
   - hermano(X,Y): X e Y comparten al menos un progenitor y X≠Y (incluye medio hermanos).
   - abuelo(A,N): A es progenitor de un progenitor de N.
   - tío(T,S): T es hermano de un progenitor de S.
   - descendiente(D,A): D es hijo de A, o hijo de un descendiente de A (recursivo).
   - ancestro: relación inversa de descendiente.
   - Los nombres romanos son alias del personaje griego.
   - Categorías: olimpico = dios olímpico; ctonico = divinidad del inframundo; dios menor, titan y
     primordial también son divinidades; semidios = hijo de dios y mortal; criatura = monstruo.

BASE DE CONOCIMIENTO (una ficha por personaje):
"""


def cargar_env(ruta: Path = RAIZ / ".env") -> None:
    """Carga un archivo .env simple (CLAVE=valor) sin dependencias externas."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea and not linea.startswith("#") and "=" in linea:
            clave, valor = linea.split("=", 1)
            os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


def base_de_conocimiento() -> str:
    """Hechos de kb.pl como texto. Si no hay SWI-Prolog, entrega el archivo fuente."""
    swipl = shutil.which("swipl")
    if swipl:
        proc = subprocess.run(
            [swipl, "-q", "-g", "exportar", "-t", "halt", str(EXPORTADOR)],
            capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return proc.stdout.strip()
    return "(Hechos en sintaxis Prolog)\n" + KB.read_text(encoding="utf-8")


def configuracion() -> tuple[str, str, str, str | None]:
    cargar_env()
    proveedor = os.getenv("LLM_PROVIDER", "openai").lower()
    if proveedor not in PROVEEDORES:
        raise RuntimeError(f"LLM_PROVIDER inválido: {proveedor}. Opciones: {', '.join(PROVEEDORES)}")
    url, var_clave, modelo = PROVEEDORES[proveedor]
    url = os.getenv("LLM_BASE_URL", url)
    modelo = os.getenv("LLM_MODEL", modelo)
    clave = os.getenv("LLM_API_KEY") or (os.getenv(var_clave) if var_clave else None)
    if var_clave and not clave:
        raise RuntimeError(f"Falta la clave de API: define {var_clave} o LLM_API_KEY en el archivo .env.")
    return proveedor, url, modelo, clave


def _post(url: str, datos: dict, cabeceras: dict, timeout: int) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(datos).encode("utf-8"),
        headers={"Content-Type": "application/json", **cabeceras}, method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detalle = e.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"El proveedor respondió HTTP {e.code}: {detalle}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"No se pudo conectar con el proveedor LLM: {e.reason}") from e


def preguntar(pregunta: str, timeout: int = 60) -> str:
    pregunta = " ".join(pregunta.split())
    if not pregunta:
        return "Escribe una pregunta sobre mitología griega."
    proveedor, url, modelo, clave = configuracion()
    sistema = INSTRUCCIONES + base_de_conocimiento()

    if proveedor == "anthropic":
        datos = {"model": modelo, "max_tokens": 400, "temperature": 0, "system": sistema,
                 "messages": [{"role": "user", "content": pregunta}]}
        cab = {"x-api-key": clave, "anthropic-version": "2023-06-01"}
        r = _post(f"{url}/messages", datos, cab, timeout)
        texto = "".join(b.get("text", "") for b in r.get("content", []))
    else:  # API compatible con OpenAI (OpenAI, Gemini, Groq, Ollama)
        datos = {"model": modelo, "temperature": 0, "max_tokens": 400,
                 "messages": [{"role": "system", "content": sistema},
                              {"role": "user", "content": pregunta}]}
        cab = {"Authorization": f"Bearer {clave}"} if clave else {}
        r = _post(f"{url}/chat/completions", datos, cab, timeout)
        texto = r["choices"][0]["message"]["content"] or ""

    texto = texto.strip()
    if not texto:
        raise RuntimeError("El LLM devolvió una respuesta vacía.")
    return texto


def descripcion_modelo() -> str:
    try:
        proveedor, _, modelo, _ = configuracion()
        return f"{proveedor} / {modelo}"
    except RuntimeError:
        return "LLM no configurado"


if __name__ == "__main__":
    print(f"Chatbot LLM ({descripcion_modelo()}). Escribe 'salir' para terminar.")
    while True:
        try:
            q = input("> ").strip()
        except EOFError:
            break
        if q.lower() in {"salir", "exit", "chao"}:
            break
        if q:
            try:
                print(preguntar(q))
            except RuntimeError as e:
                print(f"[Error] {e}")
