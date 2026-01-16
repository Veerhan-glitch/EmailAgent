import logging
import subprocess

logger = logging.getLogger(__name__)


class LLMAdapter:
    """
    Gemini-first, Ollama-fallback adapter.
    Gemini is attempted by caller.
    Ollama is used ONLY if Gemini fails.
    """

    def __init__(self, model: str = "llama3.1:8b"):
        self.model = model

    def generate_with_ollama(self, prompt: str) -> str | None:
        try:
            result = subprocess.run(
                ["ollama", "run", self.model],
                input=prompt.encode("utf-8"),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error(result.stderr.decode())
                return None

            return result.stdout.decode().strip()

        except Exception as e:
            logger.error(f"Ollama failed: {e}")
            return None

    def generate_compose_body(self, recipient, subject, intent) -> str:
        # Normalize recipients to list
        recipients = recipient if isinstance(recipient, list) else [recipient]

        greeting_hint = (
            "addressed to multiple people"
            if len(recipients) > 1
            else "addressed to one person"
        )

        prompt = f"""
    Write a short, polite, professional email {greeting_hint}.

    Recipients: {", ".join(recipients)}
    Subject: {subject}
    Purpose: {intent}

    Rules:
    - Be concise
    - Friendly tone
    - No placeholders
    - No markdown
    - End with a polite closing
    - Do NOT invent names
    """
        logger.info("Using Ollama to generate compose email body")

        return self.generate_with_ollama(prompt)
