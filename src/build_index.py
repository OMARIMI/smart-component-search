import json
from pathlib import Path

import chromadb
import requests


DATA_PATH = Path("data/components.json")
DB_PATH = "chroma_db"
COLLECTION_NAME = "components"

OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODEL = "embeddinggemma"

BATCH_SIZE = 20


def create_embeddings(texts):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBED_MODEL,
            "input": texts,
        },
        timeout=300,
    )

    response.raise_for_status()

    return response.json()["embeddings"]


def record_to_text(record):
    return (
        f"Name: {record['name']}. "
        f"Category: {record['category']}. "
        f"Description: {record['description']} "
        f"Voltage range: {record['voltage_min_v']} to "
        f"{record['voltage_max_v']} volts. "
        f"Material: {record['material']}. "
        f"Size: {record['size_mm']} mm. "
        f"Estimated cost: ${record['estimated_cost_usd']}. "
        f"Keywords: {', '.join(record['keywords'])}."
    )


def main():
    records = json.loads(
        DATA_PATH.read_text(encoding="utf-8")
    )

    client = chromadb.PersistentClient(path=DB_PATH)

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start:start + BATCH_SIZE]

        texts = [
            record_to_text(record)
            for record in batch
        ]

        embeddings = create_embeddings(texts)

        ids = []
        metadatas = []

        for record in batch:
            ids.append(record["id"])

            metadatas.append(
                {
                    "name": record["name"],
                    "category": record["category"],
                    "voltage_min_v": record["voltage_min_v"],
                    "voltage_max_v": record["voltage_max_v"],
                    "material": record["material"],
                    "size_mm": record["size_mm"],
                    "estimated_cost_usd": record["estimated_cost_usd"],
                    "keywords": ", ".join(record["keywords"]),
                    "source_type": record["source_type"],
                    "source_reference": record["source_reference"],
                }
            )

        collection.upsert(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        print(
            f"Indexed {min(start + BATCH_SIZE, len(records))}"
            f"/{len(records)} components"
        )

    print()
    print("Index complete.")
    print(f"Records in Chroma: {collection.count()}")


if __name__ == "__main__":
    main()