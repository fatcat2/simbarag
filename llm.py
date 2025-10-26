import os

from ollama import Client
from openai import OpenAI

import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

TRY_OLLAMA = os.getenv("TRY_OLLAMA", False)


class LLMClient:
    def __init__(self):
        try:
            self.ollama_client = Client(
                host=os.getenv("OLLAMA_URL", "http://localhost:11434"), timeout=1.0
            )
            self.ollama_client.chat(
                model="gemma3:4b", messages=[{"role": "system", "content": "test"}]
            )
            self.PROVIDER = "ollama"
            logging.info("Using Ollama as LLM backend")
        except Exception as e:
            print(e)
            self.openai_client = OpenAI()
            self.PROVIDER = "openai"
            logging.info("Using OpenAI as LLM backend")

    def chat(
        self,
        prompt: str,
        system_prompt: str,
    ):
        # Instituting a fallback if my gaming PC is not on
        if self.PROVIDER == "ollama":
            try:
                response = self.ollama_client.chat(
                    model="gemma3:4b",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": prompt},
                    ],
                )
                output = response.message.content
                return output
            except Exception as e:
                logging.error(f"Could not connect to OLLAMA: {str(e)}")

        response = self.openai_client.responses.create(
            model="gpt-4o-mini",
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
        )
        output = response.output_text

        return output


if __name__ == "__main__":
    client = Client()
    client.chat(model="gemma3:4b", messages=[{"role": "system", "promp": "hack"}])
