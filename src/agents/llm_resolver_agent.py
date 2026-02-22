import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

class LLMResolverAgent:
    def __init__(self, config):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment")

        self.model = config["groq"]["model"]
        self.timeout = config["groq"].get("timeout", 30)
        self.max_retries = config["groq"].get("max_retries", 5)

        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def explain(self, context, conflicts):
        prompt = f"""
You are a compliance reasoning assistant.

Instructions:
- Explain BOTH interpretations neutrally
- Do NOT decide which is correct
- Do NOT hallucinate
- Use only provided data

Context:
{context}

Conflicts:
{conflicts}
"""

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a strict compliance reasoning assistant."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 800
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )

                # Handle rate limit explicitly
                if response.status_code == 429:
                    wait_time = min(2 ** attempt, 30)
                    print(f"[Groq Rate Limit] Retry {attempt}/{self.max_retries} in {wait_time}s")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                return data["choices"][0]["message"]["content"]

            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries:
                    raise RuntimeError(f"Groq API failed after retries: {e}")
                wait_time = min(2 ** attempt, 30)
                time.sleep(wait_time)

        raise RuntimeError("Groq API call failed unexpectedly")
