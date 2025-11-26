import time
import uuid
import json
import os
from pythonjsonlogger import jsonlogger
import logging
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, Gauge

load_dotenv()

LOG_PATH = os.getenv("LOG_PATH", "logs/agent.log")
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)


REQUEST_LATENCY = Histogram("agent_request_latency_seconds", "Latency of agent requests")
REQUEST_COUNT = Counter("agent_requests_total", "Total agent requests", ['status'])
TOKENS_USED = Counter("agent_tokens_used_total", "Total tokens used")

logger = logging.getLogger("agent_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(LOG_PATH)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(trace_id)s %(span_id)s %(parent_span_id)s %(message)s %(role)s %(latency_ms)s %(tokens_used)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def new_trace_id():
    return str(uuid.uuid4())

def new_span_id():
    return str(uuid.uuid4())[:8]

def log_event(trace_id, span_id, parent_span_id, role, message, latency_ms=None, tokens_used=None, tool=None, extra=None):
    record = {
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "role": role,
        "message": message,
        "tool": tool,
        "latency_ms": latency_ms,
        "tokens_used": tokens_used
    }
  
    logger.info(json.dumps(record), extra={
        "trace_id": trace_id,
        "span_id": span_id,
        "parent_span_id": parent_span_id,
        "role": role,
        "latency_ms": latency_ms or 0,
        "tokens_used": tokens_used or 0
    })

def instrument(fn):
    def wrapper(*args, **kwargs):
        trace_id = kwargs.get("trace_id") or new_trace_id()
        parent_span_id = kwargs.get("parent_span_id")
        span_id = new_span_id()
        start = time.time()
        try:
            resp = fn(*args, **kwargs, trace_id=trace_id, span_id=span_id)
            status = "success"
        except Exception as e:
            resp = None
            status = "error"
            raise
        finally:
            latency = (time.time() - start)*1000
            REQUEST_LATENCY.observe(latency/1000.0)
            REQUEST_COUNT.labels(status=status).inc()
            log_event(trace_id, span_id, parent_span_id, role="assistant", message=f"call to {fn.__name__}", latency_ms=latency, tokens_used=getattr(resp, "usage", {}).get("total_tokens", None) if resp else None)
        return resp
    return wrapper
