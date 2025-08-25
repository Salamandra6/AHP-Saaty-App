import os
from typing import Optional
from openai import OpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

def brief_explanation(recinto: str, activo: str, situacion: str, categoria: str, ic: float) -> str:
    """
    Pide a OpenAI (Responses API) una explicación breve, técnica y clara.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Falta OPENAI_API_KEY en el entorno (o .env).")

    client = OpenAI(api_key=api_key)
    prompt = (
        f"Eres un analista de riesgos. Genera una explicación técnica breve (80–120 palabras), en español, "
        f"sobre el nivel de criticidad calculado.\n\n"
        f"Contexto:\n"
        f"- Recinto: {recinto}\n"
        f"- Activo: {activo}\n"
        f"- Situación: {situacion}\n"
        f"- Nivel de criticidad: {categoria} (IC={ic:.2f})\n\n"
        f"Requisitos:\n"
        f"- Tono profesional y claro.\n"
        f"- Justifica el nivel de criticidad de forma objetiva (2–4 factores)."
        f"- No incluyas matrices, CI/CR ni fórmulas; no uses bullet points."
    )

    # Responses API: output_text agrega el texto final de forma conveniente
    # Docs oficiales: Quickstart/Responses y API reference.
    # https://platform.openai.com/docs/quickstart  |  https://platform.openai.com/docs/api-reference/responses
    resp = client.responses.create(
        model=MODEL,
        input=prompt
    )
    return resp.output_text  # propiedad de conveniencia para el texto final
