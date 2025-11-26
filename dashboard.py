import streamlit as st
import pandas as pd
import json
from datetime import datetime
import matplotlib.pyplot as plt
import os

LOG_PATH = os.getenv("LOG_PATH", "logs/agent.log")

@st.cache_data
def load_logs(path):
    rows = []
    if not os.path.exists(path):
        return pd.DataFrame(rows)
    with open(path,'r',encoding='utf-8') as f:
        for line in f:
            try:
                j = json.loads(line)
                if isinstance(j.get("message"), str):
                    try:
                        inner = json.loads(j["message"])
                        j.update(inner)
                    except:
                        pass
                rows.append(j)
            except:
                continue
    return pd.DataFrame(rows)

st.title("Dashboard Observabilidad - Agente Univ.")

df = load_logs(LOG_PATH)
st.write("Registros cargados:", len(df))

if len(df)==0:
    st.info("No hay logs. Ejecuta el agente para generar registros.")
else:
    avg_latency = df["latency_ms"].dropna().astype(float).mean()
    total_requests = len(df)
    total_tokens = df["tokens_used"].dropna().astype(float).sum()
    st.metric("Latencia media (ms)", round(avg_latency or 0,2))
    st.metric("Total registros", total_requests)
    st.metric("Tokens usados (total)", int(total_tokens or 0))


    st.subheader("Distribución latencia (ms)")
    fig, ax = plt.subplots()
    df["latency_ms"].dropna().astype(float).hist(bins=30, ax=ax)
    st.pyplot(fig)

    st.subheader("Eventos por role")
    counts = df['role'].value_counts()
    st.bar_chart(counts)


    st.subheader("Detalle por trace_id")
    trace_ids = df['trace_id'].dropna().unique().tolist()
    sel = st.selectbox("Selecciona trace_id", options=["--"]+trace_ids)
    if sel and sel!="--":
        sub = df[df['trace_id']==sel].sort_values('asctime')
        st.dataframe(sub[['asctime','role','message','latency_ms','tokens_used','tool']])
