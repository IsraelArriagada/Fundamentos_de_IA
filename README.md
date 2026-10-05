# Proyecto N°2 – Entrega 1: chatbot en Prolog (Mitología griega)
- `prolog/kb.pl`: base de conocimiento (hechos y reglas de primer orden).
- `prolog/chatbot.pl`: chatbot en Prolog.
- `informe/ENTREGA1.md`: dominio, modelado y ejemplos.
- `tests/`, `bot_prolog.py`: pruebas automáticas.

Ejecutar: `swipl -q -g main -t halt prolog/chatbot.pl` (requiere SWI-Prolog).
Pruebas: `python -m unittest tests/test_prolog.py`
Modificar conocimiento: agregar hechos en `prolog/kb.pl`; se recargan en cada pregunta.
