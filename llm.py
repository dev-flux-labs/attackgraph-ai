"""
llm.py — builds prompts and streams investigation reports from a local Ollama model.
"""

# ollama imported lazily inside generate_report() so it doesn't slow page load

# System prompt that frames the model as a SOC analyst
SYSTEM_PROMPT = """You are an experienced cybersecurity analyst working in a Security Operations Center (SOC).
You will be given a description of a security incident and relevant threat intelligence context retrieved from a knowledge base.
Your job is to produce a concise, structured investigation report.

Format your response with these exact sections:
## Incident Summary
Brief description of what likely happened based on the indicators provided.

## Key Indicators of Compromise (IOCs)
Bullet list of specific IOCs mentioned (IPs, hashes, domains, process names, etc.).
If none are explicitly mentioned, note that.

## Likely Attack Techniques
Bullet list of the probable techniques used, referencing MITRE ATT&CK IDs where applicable.

## Recommended Next Steps
Numbered list of immediate investigation and containment actions.

Be specific. Do not pad the response with generic advice."""


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Combine the retrieved chunks into a single context block for the LLM."""
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        context_parts.append(f"[Source {i}: {chunk['source']}]\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    return f"""INCIDENT DESCRIPTION:
{query}

RELEVANT THREAT INTELLIGENCE CONTEXT:
{context}

Based on the above, produce the investigation report."""


def generate_report(query: str, chunks: list[dict], model: str = "llama3.2"):
    """
    Stream an investigation report from Ollama.
    Yields text chunks as they arrive so the UI can display them incrementally.
    Raises ConnectionError if Ollama is not running.
    """
    import ollama
    prompt = build_prompt(query, chunks)

    try:
        stream = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            stream=True,
        )
        for chunk in stream:
            content = chunk["message"]["content"]
            if content:
                yield content

    except Exception as e:
        error_msg = str(e).lower()
        _unreachable = "connection" in error_msg or "refused" in error_msg or "timeout" in error_msg
        _bad_model = "not found" in error_msg or "404" in error_msg
        if _unreachable:
            raise ConnectionError(
                f"Cannot reach Ollama. Make sure it's running (`ollama serve`) "
                f"and the model is pulled (`ollama pull {model}`)."
            )
        if _bad_model:
            raise ConnectionError(
                f"Model '{model}' not found in Ollama. "
                f"Run `ollama pull {model}` to download it."
            )
        raise
