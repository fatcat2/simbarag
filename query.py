import json
import os
from typing import Literal
import datetime
from ollama import Client

from openai import OpenAI

from pydantic import BaseModel, Field

# Configure ollama client with URL from environment or default to localhost
ollama_client = Client(host=os.getenv("OLLAMA_URL", "http://localhost:11434"))

# This uses inferred filters — which means using LLM to create the metadata filters


class FilterOperation(BaseModel):
    op: Literal["$gt", "$gte", "$eq", "$ne", "$lt", "$lte", "$in", "$nin"]
    value: str | list[str]


class FilterQuery(BaseModel):
    field_name: Literal["created_date, tags"]
    op: FilterOperation


class AndQuery(BaseModel):
    op: Literal["$and", "$or"]
    subqueries: list[FilterQuery]


class GeneratedQuery(BaseModel):
    fields: list[str]
    extracted_metadata_fields: str


class Time(BaseModel):
    time: int


DOCTYPE_OPTIONS = [
    "Bill",
    "Image Description",
    "Insurance",
    "Medical Record",
    "Documentation",
    "Letter",
]


class DocumentType(BaseModel):
    type: list[str] = Field(description="type of document", enum=DOCTYPE_OPTIONS)


PROMPT = """
You are an information specialist that processes user queries. The current year is 2025. The user queries are all about 
a cat, Simba, and its records. The types of records are listed below. Using the query, extract the 
the date range the user is trying to query. You should return it as a JSON. The date tag is created_date. Return the date in epoch time.

If the created_date cannot be ascertained, set it to epoch time start.

You have several operators at your disposal:
- $gt: greater than
- $gte: greater than or equal
- $eq: equal
- $ne: not equal
- $lt: less than
- $lte: less than or equal to
- $in: in
- $nin: not in

Logical operators:
- $and, $or

### Example 1
Query: "Who is Simba's current vet?"
Metadata fields: "{"created_date"}"
Extracted metadata fields: {"created_date: {"$gt": "2025-01-01"}}

### Example 2
Query: "How many teeth has Simba had removed?"
Metadata fields: {}
Extracted metadata fields: {}

### Example 3
Query: "How many times has Simba been to the vet this year?"
Metadata fields: {"created_date"}
Extracted metadata fields: {"created_date": {"gt": "2025-01-01"}}

document_types:
- aftercare
- bill
- insurance claim
- medical records

Only return the extracted metadata fields. Make sure the extracted metadata fields are valid JSON
"""


DOCTYPE_PROMPT = f"You are an information specialist that processes user queries. A query can have two tags attached from the following options. Based on the query, determine which of the following options is most appropriate: {','.join(DOCTYPE_OPTIONS)}"


class QueryGenerator:
    def __init__(self) -> None:
        pass

    def date_to_epoch(self, date_str: str) -> float:
        split_date = date_str.split("-")
        date = datetime.datetime(
            int(split_date[0]),
            int(split_date[1]),
            int(split_date[2]),
            0,
            0,
            0,
        )

        return date.timestamp()

    def get_doctype_query(self, input: str):
        print(DOCTYPE_PROMPT)
        client = OpenAI()
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are an information specialist that is really good at deciding what tags a query should have",
                },
                {"role": "user", "content": DOCTYPE_PROMPT + " " + input},
            ],
            model="gpt-4o",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "document_type",
                    "schema": DocumentType.model_json_schema(),
                },
            },
        )

        response_json_str = response.choices[0].message.content
        type_data = json.loads(response_json_str)
        print(type_data)
        return type_data

    def get_query(self, input: str):
        client = OpenAI()
        response = client.responses.parse(
            model="gpt-4o",
            input=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": input},
            ],
            text_format=GeneratedQuery,
        )
        print(response.output)
        query = json.loads(response.output_parsed.extracted_metadata_fields)
        # response: ChatResponse = ollama_client.chat(
        # model="gemma3n:e4b",
        # messages=[
        # {"role": "system", "content": PROMPT},
        # {"role": "user", "content": input},
        # ],
        # format=GeneratedQuery.model_json_schema(),
        # )

        # query = json.loads(
        # json.loads(response["message"]["content"])["extracted_metadata_fields"]
        # )
        # date_key = list(query["created_date"].keys())[0]
        # query["created_date"][date_key] = self.date_to_epoch(
        # query["created_date"][date_key]
        # )

        # if "$" not in date_key:
        # query["created_date"]["$" + date_key] = query["created_date"][date_key]

        return query


if __name__ == "__main__":
    qg = QueryGenerator()
    print(qg.get_doctype_query("How heavy is Simba?"))
