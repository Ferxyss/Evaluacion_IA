# 🎓 Asistente Universitario Inteligente  
### Proyecto Unidad 2 – Ingeniería de Soluciones con IA (003D)

**Integrante:** Fernanda Paredes  
**Profesor:** Giocrisrai Godoy Godoy  

---

# 📌 Descripción General

El **Asistente Universitario Inteligente** es un agente conversacional avanzado diseñado para responder preguntas frecuentes de estudiantes sobre becas, notas, retiros, reglamentos, fechas académicas y otros procesos administrativos.

El sistema integra:

- **IA generativa (GPT-4o)**
- **RAG local (archivos TXT/MD)**
- **Orquestación con agentes**
- **Memoria conversacional**
- **Observabilidad avanzada**
- **Dashboard interactivo**

---

# 🧠 Objetivos del Proyecto

- Reducir tiempos de respuesta académica.
- Automatizar atención estudiantil.
- Aumentar precisión mediante recuperación de contexto (RAG).
- Implementar trazabilidad completa de interacciones.
- Medir desempeño con métricas reales: tokens, latencia, errores, etc.

---

# 🏗 Arquitectura del Sistema

El agente utiliza una arquitectura en capas:

## **1. Capa Cognitiva (GPT-4o)**
- Planificación
- Razonamiento
- Síntesis final
- Integración con subagentes

## **2. Capa de Memoria**
- 💬 *Short-term memory* (turnos recientes)
- 🧠 *Long-term simulated memory*

## **3. Capa RAG (archivos locales)**
- Segmentación en chunks
- Scoring por similitud léxica
- Retención contextual

## **4. Capa de Observabilidad**
- Logs JSON estructurados
- Dashboard local (Streamlit)
- Trazabilidad con **LangSmith**

## **5. Capa Agentes**
- Planner
- Subagente académico
- Subagente de redacción
- Subagente informativo

---

# 📁 Componentes del Proyecto

| Archivo | Función |
|--------|---------|
| `assistant_uni.py` | Núcleo del agente (RAG + razonamiento + logging). |
| `planner_agent.py` | Planificación de subagentes. |
| `memory.py` | Manejo de memoria conversacional. |
| `observability.py` | Soporte para métricas. |
| `dashboard.py` | Dashboard en Streamlit. |
| `data/` | Documentos fuente usados por RAG. |
| `logs/agent.log` | Log estructurado formato JSON. |
| `requirements.txt` | Dependencias del proyecto. |

---

# 📌 Configuración del `.env`

Tu configuración REAL incluye:

```env
OPENAI_API_KEY=ghp_xxxxxxxxxxxxxx
OPENAI_BASE_URL=https://models.inference.ai.azure.com
OPENAI_MODEL=gpt-4o

LANGSMITH_API_KEY=lsv2_xxxxxxxxxxxxxx
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=lsv2_xxxxxxxxxxxxxx

LOG_PATH=logs/agent.log
```

✔ Incluye soporte para **Azure OpenAI**  
✔ Trazabilidad avanzada activada  
✔ Se registran tokens reales o estimados

---

# ⚙ Instalación

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows
pip install -r requirements.txt
```

---

# ▶ Ejecución del Agente

```bash
python assistant_uni.py
```

Ejemplo:

```
Escribe tu pregunta o 'salir':
> ¿Cómo puedo retirar una asignatura?
```

---

# 📊 Observabilidad

Toda interacción genera logs JSON en:

```
logs/agent.log
```

Ejemplo real:

```json
{
  "trace_id": "fa1b9f71-52a0-4b54-9f9b-3c9a88fa74a3",
  "role": "assistant",
  "latency_ms": 7590.41,
  "tokens_used": 677,
  "message": "Para retirar una asignatura..."
}
```

## 📌 Importante
Ahora el sistema:

✔ **Obtiene tokens reales cuando vienen desde OpenAI**  
✔ **Usa estimación segura basada en longitud cuando no están disponibles**  
✔ **Registra tokens en todos los flujos (simple + orquestado)**  

---

# 📈 Dashboard en Streamlit

Ejecutar:

```bash
streamlit run dashboard.py
```

Acceder en:

```
http://localhost:8501
```

El dashboard muestra:

- Tokens utilizados (reales + estimados)
- Latencia por interacción
- Total de eventos
- Distribución de roles (user/system/assistant)
- Tabla detallada por trace_id

---

# 🔎 Trazabilidad en LangSmith

El sistema envía automáticamente:

- LLM Calls
- Traces
- Métricas
- Costo
- Tokens

Para revisarlo:

👉 https://smith.langchain.com

---

# 📝 Resultados

El agente es capaz de:

- Interpretar correctamente solicitudes académicas reales.
- Recuperar contexto desde documentos institucionales.
- Producir respuestas claras, fiables y citadas.
- Mantener memoria de la conversación.
- Registrar métricas completas de uso y desempeño.
- Mostrar visualizaciones en un dashboard profesional.

---

# 👩‍💻 Autora

**Fernanda Paredes**  
Ingeniería en Informática  

---

# ✔ Estado Final del Proyecto
Este proyecto implementa **todas las capacidades pedidas en la unidad**, y agrega extras avanzados como:

- Integración con LangSmith  
- Cálculo inteligente de tokens  
- Logging JSON profesional  
- Arquitectura completa con agentes  
- Dashboard real de observabilidad  

Entrega lista. 🎉

