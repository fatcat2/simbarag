import json
from typing import Literal

from ollama import chat, ChatResponse

from pydantic import BaseModel, Field

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


PROMPT = """
You are an information specialist that processes user queries. The user queries are all about 
a cat, Simba, and its records. The types of records are listed below. Using the query, extract the 
type of record the user is trying to query and the date range the user is trying to query.


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
Metadata fields: "{"created_date, tags"}"
Extracted metadata fields: {"$and": [{"created_date: {"$gt": "2025-01-01"}, "tags": {"$in": ["bill", "medical records", "aftercare"]}}]}

### Example 2
Query: "How many teeth has Simba had removed?"
Metadata fields: {"tags"}
Extracted metadata fields: {"tags": "medical records"}

### Example 3
Query: "How many times has Simba been to the vet this year?"
Metadata fields: {"tags", "created_date"}
Extracted metadata fields: {"$and": [{"created_date": {"gt": "2025-01-01"}, "tags": {"$in": ["bill"]}}]}

document_types:
- aftercare
- bill
- insurance claim
- medical records

Only return the extracted metadata fields. Make sure the extracted metadata fields are valid JSON
"""


class QueryGenerator:
    def __init__(self) -> None:
        pass

    def get_query(self, input: str):
        response: ChatResponse = chat(
            model="gemma3n:e4b",
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": input},
            ],
            format=GeneratedQuery.model_json_schema(),
        )

        print(
            json.loads(
                json.loads(response["message"]["content"])["extracted_metadata_fields"]
            )
        )


if __name__ == "__main__":
    qg = QueryGenerator()
    qg.get_query("How old is Simba?")
