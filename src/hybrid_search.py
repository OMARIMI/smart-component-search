import json
import re
from pathlib import Path

import chromadb
import requests


DATA_PATH = Path("data/components.json")
DB_PATH = "chroma_db"
COLLECTION_NAME = "components"

OLLAMA_URL = "http://127.0.0.1:11434/api/embed"
EMBED_MODEL = "embeddinggemma"

TOP_K = 5


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


def tokenize(text):
    return set(
        re.findall(
            r"[a-zA-Z0-9.]+",
            text.lower(),
        )
    )


def load_records():
    return json.loads(
        DATA_PATH.read_text(encoding="utf-8")
    )


def record_matches_filters(
    record,
    category=None,
    max_cost=None,
    target_voltage=None,
):
    if category:
        if record["category"].lower() != category.lower():
            return False

    if max_cost is not None:
        if record["estimated_cost_usd"] > max_cost:
            return False

    if target_voltage is not None:
        if not (
            record["voltage_min_v"]
            <= target_voltage
            <= record["voltage_max_v"]
        ):
            return False

    return True


def build_chroma_filter(
    category=None,
    max_cost=None,
    target_voltage=None,
):
    conditions = []

    if category:
        conditions.append(
            {
                "category": {
                    "$eq": category
                }
            }
        )

    if max_cost is not None:
        conditions.append(
            {
                "estimated_cost_usd": {
                    "$lte": max_cost
                }
            }
        )

    if target_voltage is not None:
        conditions.append(
            {
                "voltage_min_v": {
                    "$lte": target_voltage
                }
            }
        )

        conditions.append(
            {
                "voltage_max_v": {
                    "$gte": target_voltage
                }
            }
        )

    if not conditions:
        return None

    if len(conditions) == 1:
        return conditions[0]

    return {
        "$and": conditions
    }


def vector_search(
    query,
    category=None,
    max_cost=None,
    target_voltage=None,
    limit=20,
):
    client = chromadb.PersistentClient(
        path=DB_PATH
    )

    collection = client.get_collection(
        name=COLLECTION_NAME
    )

    embedding = create_embedding(query)

    where_filter = build_chroma_filter(
        category=category,
        max_cost=max_cost,
        target_voltage=target_voltage,
    )

    query_args = {
        "query_embeddings": [embedding],
        "n_results": min(
            limit,
            collection.count()
        ),
        "include": [
            "metadatas",
            "distances",
        ],
    }

    if where_filter:
        query_args["where"] = where_filter

    results = collection.query(
        **query_args
    )

    ranked = []

    for index, component_id in enumerate(
        results["ids"][0]
    ):
        ranked.append(
            {
                "id": component_id,
                "metadata": results["metadatas"][0][index],
                "distance": results["distances"][0][index],
            }
        )

    return ranked


def keyword_search(
    query,
    category=None,
    max_cost=None,
    target_voltage=None,
):
    records = load_records()

    query_terms = tokenize(query)

    ranked = []

    for record in records:

        if not record_matches_filters(
            record,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        ):
            continue

        searchable_text = " ".join(
            [
                record["name"],
                record["category"],
                record["description"],
                " ".join(
                    record["keywords"]
                ),
                record["material"],
            ]
        )

        text_terms = tokenize(
            searchable_text
        )

        score = len(
            query_terms.intersection(
                text_terms
            )
        )

        name_lower = record[
            "name"
        ].lower()

        for term in query_terms:
            if term in name_lower:
                score += 2

        if score > 0:
            ranked.append(
                {
                    "id": record["id"],
                    "record": record,
                    "score": score,
                }
            )

    ranked.sort(
        key=lambda item: (
            -item["score"],
            item["record"][
                "estimated_cost_usd"
            ],
        )
    )

    return ranked


def hybrid_search(
    query,
    category=None,
    max_cost=None,
    target_voltage=None,
):
    vector_results = vector_search(
        query=query,
        category=category,
        max_cost=max_cost,
        target_voltage=target_voltage,
        limit=20,
    )

    keyword_results = keyword_search(
        query=query,
        category=category,
        max_cost=max_cost,
        target_voltage=target_voltage,
    )

    scores = {}
    metadata_by_id = {}

    for rank, result in enumerate(
        vector_results,
        start=1,
    ):
        component_id = result["id"]

        scores.setdefault(
            component_id,
            0.0
        )

        scores[component_id] += (
            1 / (60 + rank)
        )

        metadata_by_id[
            component_id
        ] = result["metadata"]

    records = {
        record["id"]: record
        for record in load_records()
    }

    for rank, result in enumerate(
        keyword_results,
        start=1,
    ):
        component_id = result["id"]

        scores.setdefault(
            component_id,
            0.0
        )

        scores[component_id] += (
            1 / (60 + rank)
        )

        record = records[
            component_id
        ]

        metadata_by_id[
            component_id
        ] = {
            "name": record["name"],
            "category": record["category"],
            "voltage_min_v": record[
                "voltage_min_v"
            ],
            "voltage_max_v": record[
                "voltage_max_v"
            ],
            "estimated_cost_usd": record[
                "estimated_cost_usd"
            ],
        }

    ranked_ids = sorted(
        scores,
        key=lambda component_id: (
            -scores[component_id]
        ),
    )

    results = []

    for component_id in ranked_ids:
        results.append(
            {
                "id": component_id,
                "metadata": metadata_by_id[
                    component_id
                ],
                "hybrid_score": scores[
                    component_id
                ],
            }
        )

    return results


def rerank_results(
    query,
    results,
    category=None,
    max_cost=None,
    target_voltage=None,
):
    records = {
        record["id"]: record
        for record in load_records()
    }

    query_terms = tokenize(query)

    cheap_words = {
        "cheap",
        "budget",
        "affordable",
        "inexpensive",
    }

    wants_low_cost = bool(
        query_terms.intersection(
            cheap_words
        )
    )

    reranked = []

    for result in results:

        component_id = result["id"]

        if component_id not in records:
            continue

        record = records[
            component_id
        ]

        score = (
            result["hybrid_score"]
            * 100
        )

        name_terms = tokenize(
            record["name"]
        )

        category_terms = tokenize(
            record["category"]
        )

        description_terms = tokenize(
            record["description"]
        )

        name_matches = len(
            query_terms.intersection(
                name_terms
            )
        )

        category_matches = len(
            query_terms.intersection(
                category_terms
            )
        )

        description_matches = len(
            query_terms.intersection(
                description_terms
            )
        )

        score += name_matches * 4

        score += (
            category_matches * 2
        )

        score += (
            description_matches * 0.5
        )

        if category:
            if (
                record["category"].lower()
                == category.lower()
            ):
                score += 3

        if target_voltage is not None:
            if (
                record["voltage_min_v"]
                <= target_voltage
                <= record["voltage_max_v"]
            ):
                score += 3

        if max_cost is not None:
            if (
                record["estimated_cost_usd"]
                <= max_cost
            ):
                score += 2

        if wants_low_cost:

            cost = record[
                "estimated_cost_usd"
            ]

            score += (
                5 / (1 + cost)
            )

        reranked.append(
            {
                "id": component_id,
                "record": record,
                "rerank_score": score,
            }
        )

    reranked.sort(
        key=lambda item: (
            -item["rerank_score"],
            item["record"][
                "estimated_cost_usd"
            ],
        )
    )

    return reranked


def print_vector_results(results):

    print(
        "\nVECTOR-ONLY RESULTS\n"
    )

    for rank, result in enumerate(
        results[:TOP_K],
        start=1,
    ):

        metadata = result[
            "metadata"
        ]

        print(
            f"{rank}. "
            f"{metadata['name']}"
        )

        print(
            f"   ID: {result['id']}"
        )

        print(
            f"   Category: "
            f"{metadata['category']}"
        )

        print(
            f"   Voltage: "
            f"{metadata['voltage_min_v']} - "
            f"{metadata['voltage_max_v']} V"
        )

        print(
            f"   Cost: $"
            f"{metadata['estimated_cost_usd']}"
        )

        print(
            f"   Distance: "
            f"{result['distance']:.4f}"
        )

        print()


def print_keyword_results(results):

    print(
        "\nKEYWORD-ONLY RESULTS\n"
    )

    for rank, result in enumerate(
        results[:TOP_K],
        start=1,
    ):

        record = result[
            "record"
        ]

        print(
            f"{rank}. "
            f"{record['name']}"
        )

        print(
            f"   ID: "
            f"{record['id']}"
        )

        print(
            f"   Category: "
            f"{record['category']}"
        )

        print(
            f"   Voltage: "
            f"{record['voltage_min_v']} - "
            f"{record['voltage_max_v']} V"
        )

        print(
            f"   Cost: $"
            f"{record['estimated_cost_usd']}"
        )

        print(
            f"   Keyword score: "
            f"{result['score']}"
        )

        print()


def print_hybrid_results(results):

    print(
        "\nHYBRID RESULTS\n"
    )

    for rank, result in enumerate(
        results[:TOP_K],
        start=1,
    ):

        metadata = result[
            "metadata"
        ]

        print(
            f"{rank}. "
            f"{metadata['name']}"
        )

        print(
            f"   ID: "
            f"{result['id']}"
        )

        print(
            f"   Category: "
            f"{metadata['category']}"
        )

        print(
            f"   Voltage: "
            f"{metadata['voltage_min_v']} - "
            f"{metadata['voltage_max_v']} V"
        )

        print(
            f"   Cost: $"
            f"{metadata['estimated_cost_usd']}"
        )

        print(
            f"   Hybrid score: "
            f"{result['hybrid_score']:.5f}"
        )

        print()


def print_reranked_results(results):

    print(
        "\nRERANKED RESULTS\n"
    )

    for rank, result in enumerate(
        results[:TOP_K],
        start=1,
    ):

        record = result[
            "record"
        ]

        print(
            f"{rank}. "
            f"{record['name']}"
        )

        print(
            f"   ID: "
            f"{record['id']}"
        )

        print(
            f"   Category: "
            f"{record['category']}"
        )

        print(
            f"   Voltage: "
            f"{record['voltage_min_v']} - "
            f"{record['voltage_max_v']} V"
        )

        print(
            f"   Cost: $"
            f"{record['estimated_cost_usd']}"
        )

        print(
            f"   Rerank score: "
            f"{result['rerank_score']:.4f}"
        )

        print()


def optional_float(value):

    value = value.strip()

    if not value:
        return None

    return float(value)


def main():

    print(
        "\nSmart Component Search"
    )

    print(
        "Vector + keyword + hybrid + reranking"
    )

    while True:

        print()

        query = input(
            "Search query (or 'exit'): "
        ).strip()

        if query.lower() == "exit":
            break

        category = input(
            "Category filter "
            "(blank = any): "
        ).strip()

        if not category:
            category = None

        max_cost = optional_float(
            input(
                "Maximum cost "
                "(blank = any): "
            )
        )

        target_voltage = optional_float(
            input(
                "Required voltage "
                "(blank = any): "
            )
        )

        vector_results = vector_search(
            query=query,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        )

        keyword_results = keyword_search(
            query=query,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        )

        hybrid_results = hybrid_search(
            query=query,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        )

        reranked_results = rerank_results(
            query=query,
            results=hybrid_results,
            category=category,
            max_cost=max_cost,
            target_voltage=target_voltage,
        )

        print_vector_results(
            vector_results
        )

        print_keyword_results(
            keyword_results
        )

        print_hybrid_results(
            hybrid_results
        )

        print_reranked_results(
            reranked_results
        )


if __name__ == "__main__":
    main()