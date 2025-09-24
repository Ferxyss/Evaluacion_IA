import os
from dotenv import load_dotenv
from openai import OpenAI

# 1. Cargar variables del archivo .env
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")

# 2. Configurar cliente
client = OpenAI(api_key=api_key, base_url=base_url)

# 3. Función principal de consulta
def consultar(pregunta: str) -> str:
    """
    Recibe una pregunta del estudiante y devuelve la respuesta del asistente universitario.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.5,
            messages=[
                {"role": "system", "content": "Eres un asistente universitario que responde dudas académicas de manera clara y útil."},
                {"role": "user", "content": pregunta}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error al procesar la consulta: {e}"

# 4. Ejemplo de uso
if __name__ == "__main__":
    print("Asistente universitario listo ✅")
    pregunta = input("Escribe tu pregunta: ")
    respuesta = consultar(pregunta)
    print("\nPregunta:", pregunta)
    print("Respuesta:", respuesta)