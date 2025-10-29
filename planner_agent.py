from typing import List, Dict, Tuple, Callable
from openai import OpenAI


RetrieveFn = Callable[[str, int, str], List[Tuple[str, str]]]
FormatFn   = Callable[[List[Tuple[str, str]]], str]

SYSTEM_PROMPT = (
    "Eres un asistente universitario institucional. "
    "Usa el bloque 'Contexto RAG' para fundamentar y cita las fuentes del bloque entre corchetes [Fuente: archivo]. "
    "Si hay riesgo de fechas/plazos variables, indica validar en la fuente oficial."
)

class BaseAgent:
    def __init__(self, client: OpenAI, model: str, retrieve: RetrieveFn, format_ctx: FormatFn, domain_hint: str = ""):
        self.client = client
        self.model = model
        self.retrieve = retrieve
        self.format_ctx = format_ctx
        self.domain_hint = domain_hint

    def answer(self, question: str, mem_summary: str) -> str:
        ctx_pairs = self.retrieve(question, 3, self.domain_hint) 
        ctx_block = self.format_ctx(ctx_pairs)
        fuentes = sorted({src for (src, _) in ctx_pairs})

        msgs = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Memoria de sesión (resumen): {mem_summary}"},
            {"role": "user", "content": (
                f"Contexto RAG (fragmentos locales):\n{ctx_block}\n\n"
                f"Pregunta: {question}\n\n"
                "Responde primero en 2–3 párrafos y luego, si aplica, da pasos prácticos numerados. "
                "Cuando corresponda, cita fuentes entre [Fuente: archivo]."
            )},
        ]
        resp = self.client.chat.completions.create(model=self.model, temperature=0.5, messages=msgs)
        text = resp.choices[0].message.content


        if fuentes:
            text += "\n\nFuentes: " + ", ".join(f"[{f}]" for f in fuentes)
        else:
            text += "\n\n*No se encontraron fragmentos locales; valida en el sitio oficial.*"

        return text

KEYS_BECAS = ("beca", "beneficio", "arancel", "alimentación", "postulación")
KEYS_ACAD  = ("nota", "apelar", "retiro", "asignatura", "convalid", "reprob", "examen")
KEYS_ADMIN = ("certificado", "secretaría", "horario", "correo", "formulario", "oficina")

def classify_domains(q: str) -> List[str]:
    q = q.lower()
    doms = []
    if any(k in q for k in KEYS_BECAS): doms.append("becas")
    if any(k in q for k in KEYS_ACAD):  doms.append("academico")
    if any(k in q for k in KEYS_ADMIN): doms.append("admin")
    return doms or ["academico"]

def make_plan(question: str, domains: List[str]) -> List[str]:
    steps = [f"Analizar intención: {question}"]
    for d in domains:
        if d == "becas":
            steps += ["Revisar requisitos y plazos", "Listar documentos a presentar"]
        if d == "academico":
            steps += ["Revisar procedimiento (apelación/retiro)", "Verificar plazos máximos"]
        if d == "admin":
            steps += ["Definir canal formal (correo/formulario)", "Entregar horarios/contactos"]
    steps.append("Sintetizar y priorizar acciones")
    seen, plan = set(), []
    for s in steps:
        if s not in seen:
            seen.add(s); plan.append(s)
    return plan


# --- Orquestación ---
ORCH_SYS = (
    "Eres el ORQUESTADOR. Coordina agentes especializados y entrega una respuesta final priorizada. "
    "Extrae de las respuestas parciales las fuentes citadas y añádelas al final como 'Fuentes: ...'."
)

def orchestrate(question: str,
                mem_summary: str,
                client: OpenAI,
                model: str,
                retrieve: RetrieveFn,
                format_ctx: FormatFn) -> str:
    domains = classify_domains(question)
    plan = make_plan(question, domains)

    agents: Dict[str, BaseAgent] = {
        "becas":     BaseAgent(client, model, retrieve, format_ctx, domain_hint="beca"),
        "academico": BaseAgent(client, model, retrieve, format_ctx, domain_hint="reglamento"),
        "admin":     BaseAgent(client, model, retrieve, format_ctx, domain_hint="admin"),
    }

    partials: List[str] = []
    for d in domains:
        ans = agents[d].answer(question, mem_summary)
        partials.append(f"[{d.upper()}]\n{ans}")

    fusion_prompt = (
        "Plan sugerido:\n- " + "\n- ".join(plan) +
        "\n\nRespuestas parciales (incluyen posibles 'Fuentes: ...'):\n\n" + "\n\n".join(partials) +
        "\n\nEntrega una respuesta final única, clara y priorizada (2–3 párrafos, con pasos concretos). "
        "Al final, agrega una línea 'Fuentes: [archivo1], [archivo2]' extraída de las parciales; "
        "si no hay fuentes, indica validar en el sitio oficial."
    )

    msgs = [
        {"role": "system", "content": ORCH_SYS},
        {"role": "user", "content": fusion_prompt},
    ]
    resp = client.chat.completions.create(model=model, temperature=0.4, messages=msgs)
    return resp.choices[0].message.content
