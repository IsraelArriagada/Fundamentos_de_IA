"""Chatbot v1: logica de primer orden. Invoca SWI-Prolog (prolog/chatbot.pl)."""
import shutil
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parent / "prolog" / "chatbot.pl"


def preguntar(pregunta: str, timeout: int = 15) -> str:
    swipl = shutil.which("swipl")
    if swipl is None:
        raise RuntimeError("SWI-Prolog no está instalado (comando 'swipl' no encontrado).")
    entrada = " ".join(pregunta.split()) + "\n"
    proc = subprocess.run(
        [swipl, "-q", "-g", "main", "-t", "halt", str(SCRIPT)],
        input=entrada, capture_output=True, text=True, encoding="utf-8", timeout=timeout,
    )
    salida = proc.stdout.strip()
    if not salida:
        raise RuntimeError(f"Prolog no devolvió respuesta: {proc.stderr.strip()[:300]}")
    return salida
