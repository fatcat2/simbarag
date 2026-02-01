import os
import logging

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)


class LLMClient:
    def __init__(self):
        llama_url = os.getenv("LLAMA_SERVER_URL")
        if llama_url:
            self.client = OpenAI(base_url=llama_url, api_key="not-needed")
            self.model = os.getenv("LLAMA_MODEL_NAME", "llama-3.1-8b-instruct")
            self.PROVIDER = "llama_server"
            logging.info("Using llama_server as LLM backend")
        else:
            self.client = OpenAI()
            self.model = "gpt-4o-mini"
            self.PROVIDER = "openai"
            logging.info("Using OpenAI as LLM backend")

    def chat(
        self,
        prompt: str,
        system_prompt: str,
    ):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content


if __name__ == "__main__":
    client = LLMClient()
    print(client.chat(prompt="Hello!", system_prompt="You are a helpful assistant."))
