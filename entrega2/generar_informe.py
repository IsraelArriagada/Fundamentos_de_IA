"""Genera el informe final (Word) a partir de informe/resultados.json.

Uso:  python evaluar.py  &&  python generar_informe.py
Salida: informe/Informe_Final_Chatbot_Mitologia.docx
Los textos que dependen de los resultados (aciertos, fallos, tiempos) se
escriben a partir de los datos, por lo que el informe refleja la ultima evaluacion.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).parent
RESULTADOS = RAIZ / "informe" / "resultados.json"
SALIDA = RAIZ / "informe" / "Informe_Final_Chatbot_Mitologia.docx"

INTEGRANTES = ["Israel Arriagada"]
REPO = "https://github.com/IsraelArriagada/Fundamentos_de_IA"
FECHA_ENTREGA = "Domingo 15 de noviembre de 2026"

AZUL = RGBColor(0x1D, 0x4E, 0x89)
ROJO = RGBColor(0xB0, 0x1E, 0x1E)
GRIS = RGBColor(0x55, 0x5B, 0x66)


# ---------------------------------------------------------------- utilidades
def sombrear(celda, color_hex: str) -> None:
    tc_pr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color_hex)
    tc_pr.append(shd)


def tabla(doc, encabezado: list[str], filas: list[list[str]], anchos_cm: list[float], fuente: int = 9):
    t = doc.add_table(rows=1, cols=len(encabezado))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, texto in enumerate(encabezado):
        c = t.rows[0].cells[i]
        c.text = ""
        run = c.paragraphs[0].add_run(texto)
        run.bold = True
        run.font.size = Pt(fuente)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        sombrear(c, "1D4E89")
    for fila in filas:
        celdas = t.add_row().cells
        for i, texto in enumerate(fila):
            celdas[i].text = ""
            run = celdas[i].paragraphs[0].add_run(str(texto))
            run.font.size = Pt(fuente)
            if texto == "✗":
                run.font.color.rgb = ROJO
                run.bold = True
            elif texto == "✓":
                run.font.color.rgb = RGBColor(0x1B, 0x7A, 0x3A)
                run.bold = True
    t.autofit = False
    grid = t._tbl.tblGrid
    for i, col in enumerate(grid.findall(qn("w:gridCol"))):
        col.set(qn("w:w"), str(int(anchos_cm[i] * 567)))
    for fila in t.rows:
        for i, ancho in enumerate(anchos_cm):
            fila.cells[i].width = Cm(ancho)
    doc.add_paragraph()
    return t


def viñetas(doc, items: list[str]) -> None:
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        if "::" in item:
            negrita, resto = item.split("::", 1)
            p.add_run(negrita + ":").bold = True
            p.add_run(" " + resto.strip())
        else:
            p.add_run(item)


def pendiente(doc, texto: str) -> None:
    run = doc.add_paragraph().add_run(f"[Pendiente] {texto}")
    run.italic = True
    run.font.color.rgb = ROJO


def conteos_kb() -> dict[str, int]:
    preds = ["ficha/3", "progenitor/2", "categoria/2", "pareja/2", "dominio/2", "simbolo/2",
             "residencia/2", "romano/2", "mato/2", "hazana/2", "descripcion/2"]
    swipl = shutil.which("swipl")
    if not swipl:
        return {}
    meta = ("consult('prolog/kb.pl'), forall(member(P/A,[" + ",".join(preds) + "]), "
            "(functor(H,P,A), aggregate_all(count,H,N), format('~w/~w ~w~n',[P,A,N])))")
    out = subprocess.run([swipl, "-q", "-g", meta, "-t", "halt"], cwd=RAIZ,
                         capture_output=True, text=True, encoding="utf-8").stdout
    return {l.split()[0]: int(l.split()[1]) for l in out.splitlines() if l.strip()}


def marca(r: dict | None) -> str:
    if not r:
        return "—"
    if r.get("error"):
        return "⚠"
    return "✓" if r["correcta"] else "✗"


def truncada(r: dict | None) -> bool:
    """Respuesta cortada por el limite de tokens: no termina en signo de cierre."""
    t = (r or {}).get("respuesta", "").rstrip()
    return bool(t) and not t.endswith((".", "!", "?", ")", "»", '"', "”"))


def lista_fallos(filas, motor) -> list[dict]:
    return [f for f in filas if motor in f and f[motor]["correcta"] is False]


# ---------------------------------------------------------------- informe
def construir(datos: dict) -> Document:
    filas = datos["filas"]
    res = datos["resumen"]
    hay_llm = "llm" in res and res["llm"]["evaluadas"] > 0
    k = conteos_kb()

    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.2)
        s.top_margin = s.bottom_margin = Cm(2)
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(11)
    for nivel, tam in [("Heading 1", 15), ("Heading 2", 12.5)]:
        st = doc.styles[nivel]
        st.font.name = "Calibri"
        st.font.size = Pt(tam)
        st.font.color.rgb = AZUL
        st.paragraph_format.space_before = Pt(14)
        st.paragraph_format.space_after = Pt(6)
        st.paragraph_format.keep_with_next = True

    # ----- portada
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Ingeniería Civil Informática · Fundamentos de Inteligencia Artificial")
    r.font.color.rgb = GRIS
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Proyecto N°2 – Informe final")
    r.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = AZUL
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Agente inteligente que usa conocimiento: chatbot de mitología griega "
              "en lógica de primer orden (Prolog) y con un LLM (Python)").italic = True
    tabla(doc, ["Campo", "Detalle"], [
        ["Integrantes", ", ".join(INTEGRANTES)],
        ["Dominio", "Mitología griega"],
        ["Entrega", FECHA_ENTREGA],
        ["Repositorio", REPO],
        ["Evaluación ejecutada", datos["fecha"] + (f" · LLM: {datos['modelo_llm']}" if datos.get("modelo_llm") else "")],
    ], [4, 12.5], fuente=10)

    # ----- 1
    doc.add_heading("1. Dominio y justificación", 1)
    doc.add_paragraph("Elegimos la mitología griega, un dominio no relacionado con la informática, por tres razones:")
    viñetas(doc, [
        "Es cerrado y verificable:: los personajes y sus relaciones están documentados en fuentes clásicas "
        "(seguimos la Teogonía de Hesíodo), por lo que cada respuesta se puede comprobar.",
        "Tiene una estructura relacional rica:: las genealogías permiten que de un solo hecho base "
        "(progenitor/2) se deriven muchas relaciones mediante reglas, incluida una recursiva. Es el caso "
        "ideal para lógica de primer orden.",
        "Permite una comparación justa:: los dos chatbots usan exactamente la misma base de conocimiento, "
        "así la diferencia de desempeño se debe al mecanismo de razonamiento y no a los datos.",
    ])

    # ----- 2
    doc.add_heading("2. Modelado del conocimiento en lógica de primer orden", 1)
    if k:
        doc.add_paragraph(
            f"Todo el conocimiento está en un único archivo, prolog/kb.pl: {k.get('ficha/3', 0)} entidades, "
            f"{k.get('progenitor/2', 0)} relaciones de filiación, {k.get('categoria/2', 0)} categorizaciones, "
            f"{k.get('dominio/2', 0)} dominios, {k.get('simbolo/2', 0)} símbolos, {k.get('residencia/2', 0)} "
            f"residencias, {k.get('romano/2', 0)} equivalentes romanos, {k.get('mato/2', 0)} enfrentamientos, "
            f"{k.get('hazana/2', 0)} hazañas y {k.get('descripcion/2', 0)} descripciones.")
    doc.add_heading("2.1 Hechos (predicados base)", 2)
    tabla(doc, ["Predicado", "Significado"], [
        ["ficha(Id, Nombre, Género)", "Entidad, nombre para mostrar y género (m / f)"],
        ["categoria(Id, Cat)", "primordial, titan, olimpico, ctonico, dios_menor, semidios, heroe, mortal, ninfa, nereida, criatura"],
        ["progenitor(P, H)", "P es padre o madre de H: hecho base de toda la genealogía"],
        ["pareja(A, B)", "Matrimonio o unión reconocida"],
        ["dominio/2, simbolo/2, residencia/2, romano/2", "Atributos de cada divinidad"],
        ["mato(Héroe, Criatura), hazana(Héroe, Texto)", "Enfrentamientos y hazañas"],
        ["descripcion(Id, Texto)", "Descripción breve (criaturas)"],
    ], [6, 10.5])
    doc.add_heading("2.2 Reglas", 2)
    tabla(doc, ["Relación", "Regla"], [
        ["padre / madre", "∀P,H padre(P,H) ← progenitor(P,H) ∧ masculino(P)   (madre: análoga con femenino)"],
        ["hermano", "∀X,Y hermano(X,Y) ← ∃P progenitor(P,X) ∧ progenitor(P,Y) ∧ X≠Y"],
        ["abuelo", "∀A,N abuelo(A,N) ← ∃P progenitor(A,P) ∧ progenitor(P,N)"],
        ["tío", "∀T,S tio(T,S) ← ∃P progenitor(P,S) ∧ hermano(T,P)"],
        ["casados", "∀X,Y casados(X,Y) ← pareja(X,Y) ∨ pareja(Y,X)   (simetría)"],
        ["descendiente", "descendiente(D,A) ← progenitor(A,D);  descendiente(D,A) ← ∃P progenitor(P,D) ∧ descendiente(P,A)   (recursiva)"],
    ], [3.5, 13])
    doc.add_paragraph("Decisiones de modelado:")
    viñetas(doc, [
        "Medio hermanos:: hermano/2 exige compartir al menos un progenitor, por lo que Apolo y Hermes son hermanos.",
        "Versión de Hesíodo:: Afrodita nace de Urano; por eso aparece como tía de Zeus.",
        "Categoría ctónica:: Hades y Perséfone se modelan como divinidades del inframundo (ctonico) y no como "
        "olímpicos, porque Hades no reside en el Olimpo. En la entrega 1 estaban como dios_menor, lo que era impreciso.",
        "Base extensible:: agregar conocimiento solo requiere añadir hechos; las reglas no cambian.",
    ])

    # ----- 3
    doc.add_heading("3. Chatbot en Prolog", 1)
    doc.add_paragraph(
        "El chatbot (prolog/chatbot.pl) sigue este flujo: texto → normalización (minúsculas, sin tildes ni signos, "
        "reemplazo de sinónimos) → detección de entidades (identificadores o nombres romanos) → detección de "
        "intención por palabras clave → consulta a kb.pl → respuesta en español con concordancia de género.")
    doc.add_paragraph("Tipos de pregunta soportados:")
    viñetas(doc, [
        "Familia:: padre, madre, padres, hijos (también hijos en común de dos personajes), hermanos, abuelos, "
        "tíos, descendientes, ancestros, pareja y conteo de hijos.",
        "Sí/No:: sobre relaciones (“¿Es Zeus hijo de Cronos?”, “¿Hades es hermano de Zeus?”) y categorías "
        "(“¿Es Hades un dios?”).",
        "Atributos:: dominio, símbolos, residencia, equivalente romano, hazañas, criaturas derrotadas y descripción.",
        "Búsquedas inversas y listados:: “¿Quién es el dios del mar?”, “¿Quiénes son los titanes?”.",
    ])
    doc.add_heading("3.1 Mejoras respecto de la entrega 1", 2)
    viñetas(doc, [
        "Sinónimos:: mamá/papá, progenitores, engendró, etc. (antes “¿Quién es la mamá de Atenea?” fallaba).",
        "Concordancia:: “Medusa fue derrotada por Perseo”, “Apolo es hermano de Artemisa”, “Artemisa es hija de Zeus”.",
        "Dos entidades:: “¿Quiénes son los hijos de Zeus y Hera?” entrega solo los hijos en común.",
        "Orden flexible:: las preguntas de sí/no se reconocen tanto “¿Es A … de B?” como “¿A es … de B?”.",
        "Recarga real de la base:: el chatbot interactivo detecta si kb.pl cambió (fecha de modificación) y lo "
        "recarga antes de responder; así se puede modificar el conocimiento durante la demostración sin reiniciar.",
        "Errores visibles:: los errores internos se informan por la salida de error en vez de ocultarse.",
        "Pruebas:: de 6 a 24 pruebas automáticas que cubren todas las intenciones.",
    ])

    # ----- 4
    doc.add_heading("4. Chatbot con LLM (Python)", 1)
    doc.add_paragraph(
        "El chatbot LLM (bot_llm.py) usa el mismo conocimiento sin duplicarlo. En cada pregunta, "
        "prolog/exportar.pl convierte los hechos de kb.pl en una ficha de texto por personaje, con solo los "
        "hechos directos y sin aplicar reglas. Esa ficha se entrega al modelo como contexto, junto con "
        "instrucciones que:")
    viñetas(doc, [
        "le prohíben usar conocimiento externo y le indican una respuesta fija cuando el dato no está en la base;",
        "le describen en lenguaje natural las mismas reglas de primer orden (hermano, abuelo, tío, descendiente…), "
        "de modo que el LLM debe razonar igual que Prolog;",
        "fijan el formato: español, breve, “Sí/No” al inicio en preguntas cerradas y listas completas.",
    ])
    doc.add_paragraph(
        "Se usa temperatura 0 para reducir la variabilidad y cada pregunta es independiente, como en Prolog. "
        "El cliente usa solo la biblioteca estándar y funciona con cualquier API compatible con OpenAI "
        "(OpenAI, Gemini, Groq, Ollama local) o con Anthropic; el proveedor y la clave se configuran en un "
        "archivo .env que no se sube al repositorio.")

    # ----- 5
    doc.add_heading("5. Interfaz web", 1)
    doc.add_paragraph(
        "La interfaz (app.py con Flask y web/index.html) es una página de chat con tres modos: Prolog, LLM y "
        "“Comparar ambos”, que envía la pregunta a los dos motores en paralelo y muestra las respuestas lado a "
        "lado con su tiempo. El backend expone POST /api/preguntar, valida la entrada (pregunta vacía, largo "
        "máximo, motor inválido) y devuelve los errores como mensajes, sin que la aplicación se caiga.")

    # ----- 6
    doc.add_heading("6. Evaluación de desempeño", 1)
    doc.add_paragraph(
        "Se diseñó un set de 20 preguntas que cubre distintos tipos de capacidad: hechos directos, reglas simples, "
        "compuestas y recursivas, búsquedas inversas, alias, preguntas de sí/no verdaderas y falsas, conteo, "
        "preguntas con dos entidades, paráfrasis, un dato ausente en la base y una pregunta fuera del dominio. "
        "El script evaluar.py ejecuta las 20 preguntas en ambos chatbots, mide el tiempo y verifica cada "
        "respuesta con palabras clave: nombres que deben aparecer, nombres que no deben aparecer y, en las "
        "preguntas cerradas, que la respuesta comience con Sí o No. La verificación automática se complementa con una revisión manual de cada respuesta.")
    doc.add_heading("6.1 Resumen", 2)
    filas_res = []
    for m, nombre in [("prolog", "Prolog"), ("llm", "LLM")]:
        if m in res and res[m]["evaluadas"]:
            r = res[m]
            filas_res.append([nombre, f"{r['correctas']}/{r['evaluadas']}",
                              f"{100 * r['correctas'] / r['evaluadas']:.0f} %", f"{r['tiempo_promedio']} s"])
        else:
            filas_res.append([nombre, "pendiente", "—", "—"])
    tabla(doc, ["Chatbot", "Correctas", "Precisión", "Tiempo promedio"], filas_res, [4, 4, 4, 4.5], fuente=10)
    if not hay_llm:
        pendiente(doc, "Configurar el LLM en .env y ejecutar «python evaluar.py» y luego «python generar_informe.py» "
                       "para completar la columna del LLM y el análisis comparativo.")

    doc.add_heading("6.2 Preguntas y respuestas", 2)
    filas_t = []
    for f in filas:
        rp = f.get("prolog")
        rl = f.get("llm")
        txt_l = (rl["respuesta"] or ("No evaluada: cuota de la API agotada (HTTP 429)." if "429" in rl["error"]
                                      else f"No evaluada: {' '.join(rl['error'].split())[:80]}…")) if rl else "(pendiente)"
        filas_t.append([str(f["n"]), f["pregunta"], f["tipo"], rp["respuesta"], marca(rp), txt_l, marca(rl)])
    tabla(doc, ["#", "Pregunta", "Tipo", "Respuesta Prolog", "", "Respuesta LLM", ""], filas_t,
          [0.7, 3.2, 2.2, 4.6, 0.7, 4.6, 0.7], fuente=8)

    # ----- 7
    doc.add_heading("7. Análisis de desempeño", 1)
    rp = res["prolog"]
    fallos_p = lista_fallos(filas, "prolog")
    doc.add_heading("7.1 Chatbot Prolog", 2)
    texto = (f"El chatbot Prolog respondió correctamente {rp['correctas']} de {rp['evaluadas']} preguntas, con un "
             f"tiempo promedio de {rp['tiempo_promedio']} s, incluido el inicio del proceso de SWI-Prolog. "
             "Sus respuestas son exactas cuando reconoce la intención: las reglas se aplican de forma completa "
             "(los 18 descendientes de Cronos, incluido el bisnieto Tritón) y, ante un dato ausente o una pregunta "
             "fuera del dominio, lo declara en vez de inventar. ")
    if fallos_p:
        texto += "Falló en: " + "; ".join(f"pregunta {f['n']} ({f['tipo'].lower()})" for f in fallos_p) + ". "
    if any(f["n"] == 18 for f in fallos_p):
        texto += ("El caso típico es la pregunta 18, “¿Quién robó el fuego…?”: no nombra a ningún personaje, y la "
                  "palabra “fuego” activa la búsqueda inversa por dominio, por lo que responde Hefesto en lugar de "
                  "Prometeo. Es una respuesta segura en apariencia pero incorrecta, y muestra el límite de la detección "
                  "por palabras clave.")
    doc.add_paragraph(texto)
    doc.add_paragraph(
        "Advertencia metodológica: el set fue diseñado por el equipo y el chatbot Prolog se corrigió después de la "
        "entrega 1 justamente en varios de estos tipos de pregunta, así que su precisión en el set sobreestima la "
        "que tendría con preguntas nuevas. Con paráfrasis fuera del set falla con frecuencia; por ejemplo:")
    viñetas(doc, [
        "“¿Qué dios lanza rayos?”:: no la responde, porque “rayos” no coincide con “rayo” (no hay lematización).",
        "“¿Quién le cortó la cabeza a Medusa?”:: entrega la ficha de Medusa en vez de nombrar a Perseo.",
        "“¿Cuál es la relación entre Zeus y Apolo?”:: entrega la ficha de Zeus; no existe esa intención.",
    ])

    doc.add_heading("7.2 Chatbot LLM", 2)
    if hay_llm:
        rl = res["llm"]
        fallos_l = lista_fallos(filas, "llm")
        errores = (f" ({rl['errores']} pregunta{'s' if rl['errores'] > 1 else ''} no se pudo evaluar por "
                   "un error de la API)") if rl["errores"] else ""
        texto = (f"El chatbot LLM ({datos.get('modelo_llm')}) respondió correctamente {rl['correctas']} de "
                 f"{rl['evaluadas']} preguntas, con un tiempo promedio de {rl['tiempo_promedio']} s{errores}. ")
        if fallos_l:
            texto += "Falló en: " + "; ".join(f"pregunta {f['n']} ({f['tipo'].lower()})" for f in fallos_l) + ". "
        else:
            texto += "No falló ninguna pregunta del set. "
        doc.add_paragraph(texto)
        obs = []
        por_n = {f["n"]: f for f in filas}

        def ok(n):
            return por_n[n].get("llm", {}).get("correcta")

        def cortada(*ns):
            return any(ok(n) is False and truncada(por_n[n].get("llm")) for n in ns)

        def no_evaluada(n):
            return ok(n) is None
        obs.append("Paráfrasis sin entidad (18):: " + (
            "el LLM entendió la pregunta y respondió Prometeo, donde Prolog falló." if ok(18)
            else "tampoco la resolvió correctamente."))
        obs.append("Regla recursiva (6):: " + (
            "enumeró correctamente los 18 descendientes de Cronos." if ok(6)
            else "la respuesta quedó cortada por el límite de tokens (ver nota), por lo que no se puede "
                 "juzgar su razonamiento." if cortada(6)
            else "omitió o agregó personajes al enumerar los descendientes de Cronos; las listas largas derivadas "
                 "por varias reglas son su punto débil."))
        obs.append("Reglas compuestas (4 y 5):: " + (
            "aplicó bien las reglas de abuelo y tío." if ok(4) and ok(5)
            else "las respuestas quedaron cortadas por el límite de tokens (ver nota)." if cortada(4, 5)
            else "cometió errores al encadenar reglas (abuelos o tíos), a pesar de tenerlas descritas."))
        obs.append("Conteo (15):: " + ("contó bien los 11 hijos de Zeus." if ok(15) else "contó mal los hijos de Zeus."))
        obs.append("Dato ausente (19):: " + (
            "declaró no tener la información, sin inventar al padre de Teseo." if ok(19)
            else "no se pudo evaluar por un error de la API." if no_evaluada(19)
            else "respondió con conocimiento externo (alucinación respecto de la base): el padre de Teseo no está "
                 "en kb.pl."))
        obs.append("Fuera de dominio (20):: " + ("rechazó la pregunta correctamente." if ok(20) else "respondió fuera del dominio."))
        viñetas(doc, obs)
        cortadas = [f["n"] for f in filas if f.get("llm", {}).get("correcta") is False and truncada(f["llm"])]
        con_error = [f for f in filas if f.get("llm", {}).get("error")]
        if cortadas or con_error:
            nota = "Nota sobre esta ejecución: "
            if cortadas:
                nota += (f"las respuestas a las preguntas {', '.join(map(str, cortadas))} quedaron cortadas porque el "
                         "límite de tokens de salida (400) también se consumía en el razonamiento interno del modelo; "
                         "el límite se aumentó a 4000 en bot_llm.py. ")
            if con_error:
                cuota = any("429" in f["llm"]["error"] for f in con_error)
                nota += (f"La pregunta {', '.join(str(f['n']) for f in con_error)} no se evaluó por "
                         + ("agotarse la cuota gratuita de la API (error 429). " if cuota else "un error de la API. "))
            nota += "Por lo tanto, la precisión del LLM en esta ejecución está subestimada."
            p = doc.add_paragraph()
            r = p.add_run(nota)
            r.italic = True
    else:
        pendiente(doc, "Este apartado se completa automáticamente al ejecutar la evaluación con el LLM.")

    doc.add_heading("7.3 Comparación", 2)
    if hay_llm:
        rl = res["llm"]
        mejor = "Prolog" if rp["correctas"] > rl["correctas"] else ("el LLM" if rl["correctas"] > rp["correctas"] else "ninguno")
        por_n2 = {f["n"]: f for f in filas}
        solo_p = [f["n"] for f in filas if f["prolog"]["correcta"] and f.get("llm", {}).get("correcta") is False]
        solo_l = [f["n"] for f in filas if f["prolog"]["correcta"] is False and f.get("llm", {}).get("correcta")]
        txt = (f"En el set, {'ambos obtuvieron el mismo puntaje' if mejor == 'ninguno' else f'{mejor} obtuvo más aciertos'} "
               f"({rp['correctas']} contra {rl['correctas']}). ")
        if solo_p:
            txt += f"Solo Prolog acertó en {'las preguntas' if len(solo_p) > 1 else 'la pregunta'} {', '.join(map(str, solo_p))}"
            if any(truncada(por_n2[n].get("llm")) for n in solo_p):
                txt += " (en parte por respuestas del LLM cortadas, ver nota en 7.2)"
            txt += ". "
        if solo_l:
            txt += f"Solo el LLM acertó en {'las preguntas' if len(solo_l) > 1 else 'la pregunta'} {', '.join(map(str, solo_l))}. "
        if rp["tiempo_promedio"] > 0:
            txt += (f"Prolog fue unas {rl['tiempo_promedio'] / rp['tiempo_promedio']:.0f} veces más rápido "
                    f"({rp['tiempo_promedio']} s contra {rl['tiempo_promedio']} s). ")
        txt += ("En síntesis, Prolog falla “por no entender” la pregunta, mientras que el LLM entiende el lenguaje "
                "pero puede fallar “por razonar mal”, sin que la respuesta lo deje ver.")
        doc.add_paragraph(txt)
    else:
        pendiente(doc, "Comparación numérica disponible después de evaluar el LLM.")

    # ----- 8
    doc.add_heading("8. Fortalezas y debilidades", 1)
    tabla(doc, ["", "Prolog (lógica de primer orden)", "LLM restringido a la base"], [
        ["Fortalezas",
         "Respuestas exactas, completas y reproducibles. Razonamiento verificable: cada respuesta se explica por "
         "una regla. No inventa datos. Muy rápido y sin costo. El conocimiento se modifica editando hechos.",
         "Entiende paráfrasis, sinónimos, errores de escritura y preguntas sin palabras clave. Respuestas más "
         "naturales. Agregar tipos de pregunta no requiere programar nuevas intenciones."],
        ["Debilidades",
         "Solo entiende las formas de preguntar programadas (palabras clave); ante una paráfrasis puede responder "
         "otra cosa con apariencia de certeza. Cada intención nueva requiere código. Sin contexto conversacional.",
         "No determinista y no verificable: puede omitir elementos en listas largas o razonar mal al encadenar "
         "reglas. Riesgo de usar conocimiento externo. Más lento, depende de un servicio externo y tiene costo. "
         "El contexto crece con la base, lo que limita su escalabilidad."],
    ], [2.5, 7, 7], fuente=9)

    # ----- 9
    doc.add_heading("9. Conclusiones", 1)
    viñetas(doc, [
        "La lógica de primer orden es adecuada para este dominio:: con un único hecho base y cinco reglas se "
        "responden preguntas genealógicas complejas de forma exacta y explicable.",
        "El cuello de botella de Prolog es el lenguaje natural, no el razonamiento:: cuando entiende la pregunta, "
        "acierta; cuando no, el error es de interpretación.",
        "El LLM invierte esa relación:: interpreta mejor el lenguaje, pero su razonamiento no está garantizado, "
        "aun con las reglas escritas en las instrucciones.",
        "Ambos enfoques son complementarios:: la mejora más prometedora es combinarlos (sección 10).",
    ])

    # ----- 10
    doc.add_heading("10. Propuestas de mejora", 1)
    doc.add_heading("10.1 Chatbot Prolog", 2)
    viñetas(doc, [
        "Gramática DCG:: reemplazar la detección por palabras clave por una gramática de cláusulas definidas que "
        "analice la estructura de la pregunta (sujeto, relación, objeto) y evite casos como la pregunta 18.",
        "Lematización y tolerancia a errores:: reducir plurales y conjugaciones (rayos → rayo, robó → robar) y "
        "aceptar nombres mal escritos mediante distancia de edición (“Afrodta” → Afrodita).",
        "Búsqueda por hazaña y descripción:: indexar palabras de hazana/2 y descripcion/2 para responder "
        "“¿Quién robó el fuego?”.",
        "Contexto conversacional:: recordar la última entidad para preguntas como “¿y quién es su madre?”.",
        "Explicación del razonamiento:: mostrar la cadena de reglas usada (por qué Cronos es abuelo de Apolo).",
        "Nueva intención de relación:: “¿Qué relación hay entre A y B?”, buscando la relación más cercana.",
    ])
    doc.add_heading("10.2 Chatbot LLM", 2)
    viñetas(doc, [
        "Arquitectura híbrida (la más importante):: que el LLM traduzca la pregunta a una consulta Prolog "
        "(por ejemplo, abuelo(X, apolo)), que Prolog la resuelva y que el LLM redacte la respuesta. Combina la "
        "comprensión del LLM con la exactitud de las reglas.",
        "Verificación cruzada:: comparar la respuesta del LLM con la de Prolog y advertir cuando no coinciden.",
        "Recuperación selectiva (RAG):: enviar solo las fichas de los personajes mencionados y sus parientes, "
        "para que el contexto no crezca con la base.",
        "Ejemplos en las instrucciones:: incluir pocos ejemplos resueltos (few-shot) de reglas recursivas.",
    ])
    doc.add_heading("10.3 Base de conocimiento y evaluación", 2)
    viñetas(doc, [
        "Ampliar la base:: más héroes (Jasón, Odiseo), criaturas y versiones alternativas de los mitos con un "
        "predicado fuente/2 (Hesíodo, Homero).",
        "Evaluación más rigurosa:: un set mayor, con preguntas redactadas por personas ajenas al equipo y varias "
        "ejecuciones del LLM para medir su variabilidad.",
    ])

    # ----- anexo
    doc.add_heading("Anexo: ejecución", 1)
    for linea in [
        "pip install -r requirements.txt   (requiere además SWI-Prolog)",
        "cp .env.example .env   y completar el proveedor y la clave del LLM",
        "python app.py   → abrir http://127.0.0.1:5000",
        "swipl -q -g main -t halt prolog/chatbot.pl   (chatbot Prolog en consola)",
        "python bot_llm.py   (chatbot LLM en consola)",
        "python -m unittest discover tests   ·   python evaluar.py   ·   python generar_informe.py",
    ]:
        p = doc.add_paragraph(style="List Bullet")
        r = p.add_run(linea)
        r.font.name = "Consolas"
        r.font.size = Pt(9.5)
    return doc


def main() -> None:
    if not RESULTADOS.exists():
        raise SystemExit("No existe informe/resultados.json: ejecuta primero «python evaluar.py».")
    datos = json.loads(RESULTADOS.read_text(encoding="utf-8"))
    construir(datos).save(SALIDA)
    print(f"Informe generado: {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
