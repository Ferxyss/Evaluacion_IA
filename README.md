# 🎓 Asistente Universitario con GPT-4o

Este proyecto implementa un asistente universitario utilizando **GPT-4o** desde GitHub Models.  
El asistente responde preguntas académicas y de servicios estudiantiles de manera clara y útil.

---

## 🚀 Requisitos

- Python 3.10 o superior  
- Acceso a internet  
- Una API Key válida de GitHub Models (GPT-4o)  

---

## ⚙️ Instalación y configuración

### 1. Crear entorno virtual

**Windows (PowerShell):**
```bash
python -m venv .venv
.\.venv\Scripts\activate
```

**Git Bash:**
```bash
python -m venv .venv
source .venv/Scripts/activate
```

---

### 2. Instalar dependencias necesarias

```bash
pip install openai python-dotenv
```

---

### 3. Configurar las variables de entorno

Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
OPENAI_API_KEY=ghp_tu_token_generado_en_github
OPENAI_BASE_URL=https://models.inference.ai.azure.com
```
---

## ▶️ Uso

Ejecuta el script principal:  

```bash
python assistant_uni.py
```

Ejemplo de interacción:

```
Asistente universitario listo ✅
Escribe tu pregunta: ¿Cuándo comienzan las postulaciones a becas este semestre?
Respuesta: Las postulaciones comienzan en marzo y finalizan en abril.
```

---

## 📚 Tecnologías usadas

- [Python](https://www.python.org/)  
- [OpenAI GPT-4o vía GitHub Models](https://github.com/marketplace/models/azure-openai/gpt-4o)  
- [python-dotenv](https://pypi.org/project/python-dotenv/)  

---
