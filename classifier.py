import os

from llm import LLMClient

USE_OPENAI = os.getenv("OLLAMA_URL")


class Classifier:
    def __init__(self):
        self.llm_client = LLMClient()

    def classify_query_by_action(self, query):
        _prompt = "Classify the query into one of the following options: "
