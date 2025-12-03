import json
from pathlib import Path
import numpy as np
import csv
from typing import Tuple, List, Dict

LOG_PATH = Path("logs/agent.log")  
LATENCY_FIELD = "latency_ms"

def load_logs() -> List[Dict]:
    """Carga todas las líneas JSON de logs/agent.log en una lista de dicts."""
    if not LOG_PATH.exists():
        print(f"[anomaly_detector] No se encontró {LOG_PATH}")
        return []
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    items = []
    for l in lines:
        try:
            items.append(json.loads(l))
        except Exception:
            continue
    return items

def compute_percentiles(items: List[Dict], field: str = LATENCY_FIELD):
    """Calcula p50, p90, p95 y max para el campo proporcionado."""
    values = [i.get(field) for i in items if i.get(field) is not None]
    if not values:
        return {}
    arr = np.array(values)
    return {"p50": float(np.percentile(arr, 50)),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
            "max": float(arr.max())}

def detect_latency_anomalies(pct: int = 95) -> Tuple[float, List[Dict]]:
    """
    Detecta anomalías de latencia usando el percentil indicado (por defecto P95).
    Devuelve (threshold, lista_de_anomalías).
    """
    items = load_logs()
    if not items:
        return 0.0, []
    stats = compute_percentiles(items)
    threshold = stats.get(f"p{pct}", stats.get("p95", 0.0))
    anomalies = [i for i in items if i.get(LATENCY_FIELD) and i.get(LATENCY_FIELD) > threshold]
    return threshold, anomalies

def export_anomalies_csv(out_path: str = "tools/anomalies.csv", pct: int = 95):
    """Exporta las anomalías detectadas a un CSV."""
    threshold, anomalies = detect_latency_anomalies(pct)
    if not anomalies:
        print("[anomaly_detector] No se encontraron anomalías.")
        return
    keys = sorted(set().union(*(a.keys() for a in anomalies)))
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for a in anomalies:
            writer.writerow(a)
    print(f"[anomaly_detector] Exportadas {len(anomalies)} anomalías a {out_path}")

def export_anomalies_json(out_path: str = "tools/anomalies.json", pct: int = 95):
    """Exporta las anomalías detectadas a un JSON."""
    threshold, anomalies = detect_latency_anomalies(pct)
    if not anomalies:
        print("[anomaly_detector] No se encontraron anomalías.")
        return
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"threshold": threshold, "anomalies": anomalies}, f, indent=2, ensure_ascii=False)
    print(f"[anomaly_detector] Exportadas {len(anomalies)} anomalías a {out_path}")

if __name__ == "__main__":
    thr, anom = detect_latency_anomalies()
    print(f"Umbral (P95): {thr} ms — anomalías encontradas: {len(anom)}")
    if anom:
        for a in anom[:10]:
            print(a.get("trace_id"), a.get(LATENCY_FIELD))
