import chromadb
import requests


DB_PATH = "chroma_db"
COLLECTION_NAME = "components"

OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODEL = "embeddinggemma"


def create_embedding(text):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBED_MODEL,
            "input": text,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]


def search(query, top_k=5):
    client = chromadb.PersistentClient(path=DB_PATH)

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    query_embedding = create_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nSearch: {query}\n")

    for index in range(len(results["ids"][0])):
        component_id = results["ids"][0][index]
        metadata = results["metadatas"][0][index]
        distance = results["distances"][0][index]

        print(f"{index + 1}. {metadata['name']}")
        print(f"   ID: {component_id}")
        print(f"   Category: {metadata['category']}")
        print(
            f"   Voltage: {metadata['voltage_min_v']} - "
            f"{metadata['voltage_max_v']} V"
        )
        print(f"   Cost: ${metadata['estimated_cost_usd']}")
        print(f"   Distance: {distance:.4f}")
        print()


def main():
    while True:
        query = input("Search components (or 'exit'): ").strip()

        if query.lower() == "exit":
            break

        if query:
            search(query)


if __name__ == "__main__":
    main()