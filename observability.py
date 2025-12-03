import uuid
import json
import logging
import time
from typing import Optional, Dict
from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


logger = logging.getLogger("agente_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)


SOLICITUDES_TOTAL = Counter(
    'agente_solicitudes_total',
    'Cantidad total de solicitudes del agente',
    ['metodo', 'endpoint', 'estado']
)

LATENCIA_SOLICITUD = Histogram(
    'agente_latencia_s',
    'Latencia de las solicitudes en segundos',
    ['endpoint']
)

TOKENS_USADOS = Counter(
    'agente_tokens_usados_total',
    'Cantidad de tokens usados por rol',
    ['rol']
)

ERRORES = Counter(
    'agente_errores_total',
    'Errores totales por endpoint y tipo',
    ['endpoint', 'tipo_error']
)


metrics_app = FastAPI()

@metrics_app.get("/metrics")
def obtener_metricas():
    """Endpoint para exponer métricas Prometheus."""
    contenido = generate_latest()
    return Response(content=contenido, media_type=CONTENT_TYPE_LATEST)

def log_event(
    rol: str,
    mensaje: str,
    latency_ms: Optional[float] = None,
    tokens: Optional[int] = None,
    modelo: str = "gpt-4o",
    extra: Optional[Dict] = None,
    trace_id: Optional[str] = None,
    estado: str = "ok",
    error: Optional[str] = None
) -> str:
    """
    Registra un evento JSON estructurado y retorna el trace_id.
    """
    if trace_id is None:
        trace_id = str(uuid.uuid4())

    evento = {
        "trace_id": trace_id,
        "rol": rol,
        "mensaje": mensaje,
        "latencia_ms": latency_ms,
        "tokens": tokens,
        "modelo": modelo,
        "estado": estado,
        "error": error,
        "timestamp": int(time.time() * 1000)
    }

    if extra:
        evento.update(extra)

    logger.info(json.dumps(evento))
    return trace_id


def registrar_solicitud(endpoint: str, estado: str, latencia_s: float):
    """
    Registra métricas de una solicitud.
    """
    SOLICITUDES_TOTAL.labels(metodo="chat", endpoint=endpoint, estado=estado).inc()
    LATENCIA_SOLICITUD.labels(endpoint=endpoint).observe(latencia_s)


def registrar_tokens(rol: str, tokens: int):
    """
    Incrementa contador de tokens por rol.
    """
    TOKENS_USADOS.labels(rol=rol).inc(tokens)


def registrar_error(endpoint: str, tipo_error: str):
    """
    Registra error clasificado por endpoint.
    """
    ERRORES.labels(endpoint=endpoint, tipo_error=tipo_error).inc()
