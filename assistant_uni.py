import os, re, glob
from typing import List, Tuple
from dotenv import load_dotenv
from openai import OpenAI

from memory import SessionMemory
from planner_agent import orchestrate 

load_dotenv()
api_key  = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model    = os.getenv("OPENAI_MODEL", "gpt-4o")
if not api_key or not base_url:
    raise RuntimeError("Faltan OPENAI_API_KEY u OPENAI_BASE_URL en .env")
client = OpenAI(api_key=api_key, base_url=base_url)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _tokenizar(texto: str) -> List[str]:
    return re.findall(r"[a-záéíóúñ0-9]+", (texto or "").lower())

def _chunkear(texto: str, tam: int = 800, overlap: int = 120) -> List[str]:
    texto = re.sub(r"\s+", " ", (texto or "").strip())
    out, i = [], 0
    while i < len(texto):
        out.append(texto[i:i+tam])
        i += max(tam - overlap, 1)
    return out

def _cargar_documentos() -> List[Tuple[str, str]]:
    docs = []
    if not os.path.isdir(DATA_DIR):
        return docs
    for patron in ("*.txt", "*.md"):
        for path in glob.glob(os.path.join(DATA_DIR, patron)):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    docs.append((os.path.basename(path), f.read()))
            except Exception:
                continue
    return docs

def _puntuar_chunk(pregs: List[str], chunk: str) -> int:
    toks = _tokenizar(chunk)
    return sum(toks.count(t) for t in pregs)

def recuperar_contexto(pregunta: str, top_k: int = 3, domain_hint: str = "") -> List[Tuple[str, str]]:
    documentos = _cargar_documentos()
    if not documentos:
        return []
    pregs = _tokenizar(pregunta)
    candidatos: List[Tuple[int, str, str]] = []
    for fuente, contenido in documentos:
        for ch in _chunkear(contenido):
            score = _puntuar_chunk(pregs, ch)
            if domain_hint and domain_hint in fuente.lower():
                score += 4  
            if score > 0:
                candidatos.append((score, fuente, ch))
    candidatos.sort(key=lambda x: x[0], reverse=True)
    return [(fuente, ch) for _, fuente, ch in candidatos[:top_k]]

def formatear_contexto(contextos: List[Tuple[str, str]]) -> str:
    if not contextos:
        return "No se encontraron fragmentos relevantes en la base local."
    partes = []
    for fuente, frag in contextos:
        partes.append(f"[Fuente: {fuente}]\n{frag.strip()}")
    return "\n\n---\n\n".join(partes)

SYSTEM_PROMPT = (
    "Eres un asistente universitario que responde dudas académicas de manera clara y útil. "
    "Si la respuesta depende de fechas o normativas variables, indica cómo verificar en la fuente oficial. "
    "Cuando te entregue 'Contexto RAG', úsalo para responder y cita las fuentes entre [corchetes] "
    "con el nombre del archivo. Si el contexto no es suficiente, dilo y sugiere dónde confirmar."
)

def consultar(pregunta: str) -> str:
    try:
        contextos = recuperar_contexto(pregunta, top_k=3)
        bloque_contexto = formatear_contexto(contextos)
        response = client.chat.completions.create(
            model=model, temperature=0.5,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Contexto RAG (fragmentos locales):\n{bloque_contexto}\n\n"
                    f"Pregunta: {pregunta}\n\n"
                    "Responde primero en 2-3 frases y luego, si aplica, da pasos prácticos."
                )},
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al procesar la consulta: {e}"

if __name__ == "__main__":
    print("Asistente universitario listo")
    mem = SessionMemory()
    try:
        while True:
            pregunta = input("Escribe tu pregunta o 'salir' para terminar): ").strip()
            if not pregunta or pregunta.lower() == "salir":
                print("¡Hasta luego!")
                break

            if pregunta.lower().startswith("simple "):
                q = pregunta[7:].strip()
                respuesta = consultar(q)
            else:
                low = pregunta.lower()
                if "vespertina" in low: mem.remember("jornada", "vespertina")
                if "diurna"    in low:  mem.remember("jornada", "diurna")

                mem.add_turn("user", pregunta)
                respuesta = orchestrate(
                    question=pregunta,
                    mem_summary=mem.resumen(),
                    client=client,
                    model=model,
                    retrieve=recuperar_contexto,     
                    format_ctx=formatear_contexto,  
                )
                mem.add_turn("assistant", respuesta)

            print("\nPregunta:", pregunta)
            print("Respuesta:", respuesta, "\n")
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")
