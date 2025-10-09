import os

from ollama import Client
from openai import OpenAI

import typing

import logging

logging.basicConfig(level=logging.INFO)

class LLMClient:
    def __init__(self):
        try:
            self.ollama_client = ollama.Client(host=os.getenv("OLLAMA_URL", "http://localhost:11434"))
            client.chat(
                model="gemma3:4b", messages=[{"role": "system", "content": "test"}]
            )
            self.PROVIDER = "ollama"
            logging.info("Using Ollama as LLM backend")
        except:
            self.openai_client = OpenAI()
            self.PROVIDER = "openai"
            logging.info("Using OpenAI as LLM backend")

    def chat(
        self,
        prompt: str,
        system_prompt: str,
    ):
        if self.PROVIDER == "ollama":
            response = self.ollama_client.chat(
                model="gemma3:4b",
                prompt=prompt,
            )
            output = response["response"]
        elif self.PROVIDER == "openai":
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt
                    },
                ],
            )
            output = response.choices[0].message.content


if __name__ == "__main__":
    client = Client()
    client.chat(model="gemma3:4b", messages=[{"role": "system", "promp": "hack"}])
