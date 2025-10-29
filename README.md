# Asistente Universitario Inteligente

### Proyecto Unidad 2 – Ingeniería de Soluciones con IA (003D)

**Integrante:**  
- Fernanda Paredes  

**Profesor:**  
- Giocrisrai Godoy  

---

## Descripción General

El **Asistente Universitario Inteligente** es un agente conversacional diseñado para responder preguntas frecuentes de estudiantes de una universidad ficticia, tales como consultas sobre becas, notas y calendarios académicos.

Este proyecto aborda la problemática de **demoras en la atención y sobrecarga administrativa** mediante la implementación de un sistema con **IA generativa (GPT-4o)** y **frameworks de agentes** que incorporan memoria, planificación y razonamiento contextual.

---

## Objetivos del Proyecto

- Reducir los tiempos de respuesta a consultas estudiantiles.  
- Disminuir la carga administrativa de secretarías.  
- Mejorar la satisfacción y confianza de los estudiantes.  
- Garantizar transparencia en la entrega de información institucional.  

---

## Arquitectura del Sistema

El sistema está estructurado en tres capas principales:

1. **Capa Cognitiva (Core Engine – GPT-4o):**  
   Gestiona el razonamiento, la toma de decisiones y la planificación de tareas.

2. **Capa de Memoria:**  
   Almacena el contexto conversacional, permitiendo coherencia entre respuestas.  
   - *Memoria de corto plazo:* mantiene el hilo de la sesión.  
   - *Memoria de largo plazo:* conserva registros históricos simulados.

3. **Capa de Herramientas y Subagentes:**  
   Incluye módulos especializados en búsqueda, redacción y planificación.  
   - Subagente de Búsqueda (RAG)  
   - Subagente de Redacción  
   - Planner Agent  

---

## Diagrama de Orquestación

![Diagrama de orquestación](./assets/diagrama_orquestacion.png)

> **Figura:** Flujo general de orquestación entre el Usuario, el Agente Principal, los Subagentes y la Memoria.

---

## Componentes Principales del Proyecto

| Archivo | Descripción |
|----------|-------------|
| `assistant_uni.py` | Flujo principal del agente y conexión con los módulos. |
| `memory_module.py` | Manejo de memoria de corto y largo plazo. |
| `planner_agent.py` | Lógica de planificación y orquestación de tareas. |
| `.env` | Variables de entorno (OPENAI_API_KEY, BASE_URL). |
| `requirements.txt` | Lista de dependencias necesarias. |

---

## Dependencias

- `openai`
- `langchain`
- `crewai`
- `python-dotenv`

Instálalas ejecutando:

```bash
pip install -r requirements.txt
```

---

## ▶Ejecución

1. Crear y activar el entorno virtual:
   ```bash
   python -m venv .venv
   source .venv/Scripts/activate   # En Windows
   ```
2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecutar el agente:
   ```bash
   python assistant_uni.py
   ```

El sistema se probó desde **Git Bash**, entregando respuestas adaptativas en tiempo real y coherentes gracias a la memoria contextual.

---

## Resultados

Durante la validación, el agente respondió consultas como:

> **“¿Cuándo inician las postulaciones a becas?”**

**Respuesta generada:**  
> “Las fechas dependen del tipo de beca y la institución. Se recomienda revisar el calendario académico y el sitio oficial de becas.”

**Evaluación:**  
El sistema mantuvo coherencia, tono formal y redujo repeticiones, evidenciando mejoras en consistencia y trazabilidad frente al MVP inicial.

---

## Futuras Mejoras

- Integración con base de datos institucional.  
- Conexión directa con APIs académicas.  
- Persistencia completa de memoria a largo plazo.  

---

## 👩Autora

- **Fernanda Paredes** – Ingeniería de Ejecución en Informática  

---

## Referencias

- [OpenAI API Documentation](https://platform.openai.com/docs)  
- [LangChain Framework](https://python.langchain.com)  
- [CrewAI Multi-Agent Coordination Library](https://docs.crewai.io)  
- [python-dotenv Documentation](https://saurabh-kumar.com/python-dotenv)  
- [ChatGPT – OpenAI Platform](https://chat.openai.com)

---

*Proyecto desarrollado como parte de la Unidad 2 del curso “Ingeniería de Soluciones con IA”.*
