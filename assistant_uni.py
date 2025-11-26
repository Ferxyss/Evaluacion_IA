import os
import re
import glob
import time
import uuid
import json
import logging
from typing import List, Tuple, Optional
from dotenv import load_dotenv
from pythonjsonlogger import jsonlogger
from openai import OpenAI
from langsmith.wrappers import wrap_openai

from memory import SessionMemory
from planner_agent import orchestrate

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
LOG_PATH = os.getenv("LOG_PATH", "logs/agent.log")

if not API_KEY or not BASE_URL:
    raise RuntimeError("Faltan OPENAI_API_KEY u OPENAI_BASE_URL en .env")

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logger = logging.getLogger("agent_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_PATH, encoding="utf-8")
    fmt = (
        "%(asctime)s %(levelname)s %(trace_id)s %(span_id)s "
        "%(parent_span_id)s %(role)s %(latency_ms)s %(tokens_used)s %(message)s"
    )
    formatter = jsonlogger.JsonFormatter(fmt)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

def new_trace_id() -> str:
    return str(uuid.uuid4())

def new_span_id() -> str:
    return str(uuid.uuid4())[:8]

def log_event(
    trace_id: str,
    span_id: str,
    parent_span_id: Optional[str],
    role: str,
    message: str,
    latency_ms: Optional[float] = None,
    tokens_used: Optional[int] = None,
    tool: Optional[str] = None,
):
    """
    tokens_used → si viene None, se fuerza a 0.
    Esto es la causa de que antes vieras "0 tokens" siempre.
    Ahora SIEMPRE se pasa tokens reales o estimados.
    """
    rec = {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "role": role,
        "message": message,
        "tool": tool,
        "latency_ms": latency_ms or 0,
        "tokens_used": int(tokens_used) if tokens_used is not None else 0,
    }

    logger.info(
        json.dumps(rec, ensure_ascii=False),
        extra={
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id or "",
            "role": role,
            "latency_ms": latency_ms or 0,
            "tokens_used": rec["tokens_used"],
        },
    )


def _tokenizar(texto: str) -> List[str]:
    return re.findall(r"[a-záéíóúñ0-9]+", (texto or "").lower())

def _chunkear(texto: str, tam: int = 800, overlap: int = 120) -> List[str]:
    texto = re.sub(r"\s+", " ", (texto or "").strip())
    out, i = [], 0
    while i < len(texto):
        out.append(texto[i : i + tam])
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

def recuperar_contexto(
    pregunta: str, top_k: int = 3, domain_hint: str = ""
) -> List[Tuple[str, str]]:
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
    "Eres un asistente universitario que responde dudas académicas. "
    "Usa el contexto RAG cuando esté disponible. "
)

MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "2400"))
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "60"))

_blocklist_patterns = [
    r"ignora tus instrucciones",
    r"ignora todo lo anterior",
    r"salta las reglas",
    r"override",
    r"delete system prompt",
]

_request_timestamps: List[float] = []

def sanitize_input(texto: str) -> Tuple[bool, Optional[str]]:
    if not texto or not texto.strip():
        return False, "Entrada vacía."
    if len(texto) > MAX_INPUT_LENGTH:
        return False, f"Entrada demasiado larga (máx {MAX_INPUT_LENGTH} caracteres)."
    lower = texto.lower()
    for pat in _blocklist_patterns:
        if re.search(pat, lower):
            return False, "Entrada rechazada por contener instrucciones no permitidas."
    return True, None

def rate_limit_ok() -> Tuple[bool, Optional[str]]:
    global _request_timestamps
    ahora = time.time()
    window_start = ahora - 60
    _request_timestamps = [t for t in _request_timestamps if t >= window_start]
    if len(_request_timestamps) >= RATE_LIMIT_PER_MIN:
        return False, "Límite de tasa alcanzado."
    _request_timestamps.append(ahora)
    return True, None

def _extract_text_from_choice(choice) -> str:
    try:
        if isinstance(choice, dict):
            if "message" in choice:
                return choice["message"].get("content", "") or ""
            return choice.get("text", "") or ""
        if hasattr(choice, "message"):
            return getattr(choice.message, "content", "") or ""
        return getattr(choice, "text", "") or ""
    except Exception:
        return str(choice)

def _extract_tokens_used(resp) -> Optional[int]:
    """
    Intenta obtener tokens desde varias estructuras posibles.
    """
    try:
        if hasattr(resp, "usage") and resp.usage:
            total = getattr(resp.usage, "total_tokens", None)
            if total is not None:
                return int(total)
    except Exception:
        pass
    try:
        d = resp.to_dict() if hasattr(resp, "to_dict") else resp
        if isinstance(d, dict):
            usage = d.get("usage")
            if usage and usage.get("total_tokens"):
                return int(usage["total_tokens"])
    except Exception:
        pass
    return None


def consultar(pregunta: str, trace_id: Optional[str] = None, parent_span=None) -> str:
    trace_id = trace_id or new_trace_id()
    span_request = new_span_id()
    log_event(trace_id, span_request, parent_span, "user", pregunta)

    ok, err = sanitize_input(pregunta)
    if not ok:
        log_event(trace_id, new_span_id(), span_request, "system", f"input_validation_failed: {err}")
        return f"Entrada inválida: {err}"

    ok, err = rate_limit_ok()
    if not ok:
        log_event(trace_id, new_span_id(), span_request, "system", f"rate_limit: {err}")
        return f"Rate limit: {err}"

    contextos = recuperar_contexto(pregunta, top_k=3)
    bloque_contexto = formatear_contexto(contextos)

    user_content = (
        f"Contexto RAG:\n{bloque_contexto}\n\n"
        f"Pregunta: {pregunta}\n"
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    span_call = new_span_id()
    start = time.time()

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            temperature=0.5,
            messages=messages,
        )
        latency = (time.time() - start) * 1000

        text = ""
        if hasattr(resp, "choices") and resp.choices:
            text = _extract_text_from_choice(resp.choices[0])

        tokens_used = _extract_tokens_used(resp)
        if tokens_used is None:
            tokens_used = max(20, len(text) // 4)

        log_event(
            trace_id,
            span_call,
            span_request,
            "assistant",
            text,
            latency_ms=latency,
            tokens_used=tokens_used,
        )
        return text

    except Exception as e:
        latency = (time.time() - start) * 1000
        log_event(
            trace_id,
            span_call,
            span_request,
            "system",
            f"error: {e}",
            latency_ms=latency,
        )
        return f"Error al procesar la consulta: {e}"

if __name__ == "__main__":
    print("Asistente universitario listo")
    mem = SessionMemory()

    try:
        while True:
            pregunta = input("Escribe tu pregunta o 'salir': ").strip()
            if not pregunta or pregunta.lower() == "salir":
                print("¡Hasta luego!")
                break

            trace_root = new_trace_id()

    
            if pregunta.lower().startswith("simple "):
                q = pregunta[7:].strip()
                respuesta = consultar(q, trace_id=trace_root)
                print("\nPregunta:", pregunta)
                print("Respuesta:", respuesta, "\n")
                continue

            low = pregunta.lower()
            if "vespertina" in low:
                mem.remember("jornada", "vespertina")
            if "diurna" in low:
                mem.remember("jornada", "diurna")

            mem.add_turn("user", pregunta)
            span_orch = new_span_id()
            log_event(trace_root, span_orch, None, "system", "orchestrate_start")

            start_orch = time.time()

            try:
                respuesta = orchestrate(
                    question=pregunta,
                    mem_summary=mem.resumen(),
                    client=client,
                    model=MODEL,
                    retrieve=recuperar_contexto,
                    format_ctx=formatear_contexto,
                )
                latency_orch = (time.time() - start_orch) * 1000

    
                tokens_orch = None
                respuesta_text = ""

                if isinstance(respuesta, dict) and "text" in respuesta:
                    respuesta_text = respuesta.get("text", "")
                    tokens_orch = respuesta.get("tokens_used")
                else:
                    respuesta_text = str(respuesta)

        
                if not tokens_orch:
                    tokens_orch = max(20, len(respuesta_text) // 4)
                    respuesta_text = "(TOKEN_ESTIMADO) " + respuesta_text

        
                log_event(
                    trace_root,
                    new_span_id(),
                    span_orch,
                    "assistant",
                    respuesta_text,
                    latency_ms=latency_orch,
                    tokens_used=int(tokens_orch),
                )

                mem.add_turn("assistant", respuesta_text)
                print("\nPregunta:", pregunta)
                print("Respuesta:", respuesta_text, "\n")

            except Exception as e:
                latency_orch = (time.time() - start_orch) * 1000
                log_event(
                    trace_root,
                    new_span_id(),
                    span_orch,
                    "system",
                    f"orchestrate_error: {e}",
                    latency_ms=latency_orch,
                )
                print(f"Error: {e}")

    except KeyboardInterrupt:
        print("\nInterrumpido.")
