import streamlit as st
import pandas as pd
from pathlib import Path
from tools.anomaly_detector import compute_percentiles, detect_latency_anomalies, load_logs

st.set_page_config(page_title="Dashboard Observabilidad - Agente Univ.", layout="wide")
st.title("Dashboard Observabilidad - Asistente Universitario Inteligente")

LOG_PATH = Path("logs/agent.log")

@st.cache_data
def cargar_logs_df():
    items = load_logs()
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    if 'latency_ms' in df.columns:
        df['latency_ms'] = pd.to_numeric(df['latency_ms'], errors='coerce')
    return df

df = cargar_logs_df()

if df.empty:
    st.warning("No se detectaron logs en logs/agent.log. Ejecuta el agente primero.")
else:
    st.subheader("Métricas de latencia")
    stats = compute_percentiles(df.to_dict('records'), field='latency_ms')
    col1, col2, col3 = st.columns(3)
    col1.metric("P50", f"{stats.get('p50', 0):.2f} ms")
    col2.metric("P90", f"{stats.get('p90', 0):.2f} ms")
    col3.metric("P95", f"{stats.get('p95', 0):.2f} ms")

    st.markdown("**Histograma de latencia (clip a 20s para legibilidad)**")
    st.bar_chart(df['latency_ms'].clip(upper=20000).fillna(0))

    st.subheader("Distribución por rol / estado")
    if 'role' in df.columns:
        st.dataframe(df.groupby('role')['latency_ms'].describe())

    st.subheader("Anomalías detectadas (latencia > P95)")
    threshold, anomalies = detect_latency_anomalies(pct=95)
    st.write(f"Umbral P95: {threshold:.2f} ms — anomalías encontradas: {len(anomalies)}")
    if anomalies:
        anom_df = pd.DataFrame(anomalies)
        st.dataframe(anom_df.sort_values(by='latency_ms', ascending=False).head(100))

    st.subheader("Explorar interacciones por trace_id")
    if 'trace_id' in df.columns:
        trace_ids = df['trace_id'].unique().tolist()
        sel = st.selectbox("Seleccionar trace_id", options=[""] + trace_ids)
        if sel:
            st.json(df[df['trace_id'] == sel].to_dict(orient='records'))
