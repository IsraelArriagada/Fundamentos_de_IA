# Proyecto N°2 – Chatbot de Mitología Griega (Prolog + LLM)

Agente inteligente que responde preguntas sobre mitología griega de dos formas, usando **la misma base de conocimiento** (`prolog/kb.pl`):

1. **Lógica de primer orden (Prolog):** hechos + reglas (padre, hermano, abuelo, tío, descendiente recursivo).
2. **LLM (Python):** el modelo recibe los hechos de `kb.pl` y las reglas en lenguaje natural, y tiene prohibido usar conocimiento externo.

Ambos se usan desde una interfaz web que permite compararlos lado a lado.

## Estructura

| Ruta | Contenido |
|---|---|
| `prolog/kb.pl` | Base de conocimiento: hechos y reglas (fuente única) |
| `prolog/chatbot.pl` | Chatbot Prolog: normalización, entidades, intenciones, respuestas |
| `prolog/exportar.pl` | Exporta los hechos de `kb.pl` como texto para el LLM |
| `bot_prolog.py` | Puente Python → SWI-Prolog |
| `bot_llm.py` | Chatbot LLM (OpenAI, Gemini, Groq, Ollama o Anthropic; solo biblioteca estándar) |
| `app.py`, `web/index.html` | Interfaz web (Flask) |
| `evaluar.py` | Ejecuta las 20 preguntas en ambos chatbots → `informe/resultados.json` / `.md` |
| `generar_informe.py` | Genera `informe/Informe_Final_Chatbot_Mitologia.docx` desde los resultados |
| `tests/` | 24 pruebas automáticas del chatbot Prolog |

## Instalación

Requiere [SWI-Prolog](https://www.swi-prolog.org/download/stable) y Python 3.10+.

```bash
pip install -r requirements.txt
cp .env.example .env      # elegir proveedor LLM y poner la clave
```

## Uso

```bash
python app.py                                  # interfaz web → http://127.0.0.1:5000
swipl -q -g main -t halt prolog/chatbot.pl     # chatbot Prolog en consola
python bot_llm.py                              # chatbot LLM en consola
python -m unittest discover tests              # pruebas
python evaluar.py && python generar_informe.py # evaluación + informe
```

## Modificar el conocimiento

Basta con agregar hechos en `prolog/kb.pl` (ids en minúscula y sin tildes), por ejemplo:

```prolog
ficha(eaco,'Éaco',m).
progenitor(eaco,peleo).
```

Ambos chatbots ven el cambio en la siguiente pregunta, sin reiniciar: el chatbot Prolog interactivo recarga `kb.pl` si su fecha de modificación cambió, y el LLM recibe los hechos recién exportados en cada pregunta. Tras el ejemplo anterior, “¿Quiénes son los abuelos de Aquiles?” responde Éaco.
